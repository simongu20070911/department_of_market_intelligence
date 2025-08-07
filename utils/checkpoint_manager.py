# /department_of_market_intelligence/utils/checkpoint_manager.py
"""
Robust, centralized checkpoint and recovery system for the DOMI workflow.

This manager handles:
- Creating and tracking multi-step operations with fine-grained recovery.
- Saving and resuming operation progress with retries and timeouts.
- Taking snapshots of the full application state at critical junctures.
- Providing a clean interface for agents to manage long-running, fallible tasks.
"""
import os
import json
import shutil
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from dataclasses import dataclass, field, asdict
from contextlib import contextmanager

from .. import config
from .state_model import DOMISessionState
from .logger import get_logger

logger = get_logger(__name__)


@dataclass
class OperationStep:
    """Represents a single recoverable operation step."""
    step_id: str
    operation_type: str  # "file_generation", "data_processing", "experiment", etc.
    step_name: str
    input_state: Dict[str, Any]
    expected_outputs: List[str]  # Files/artifacts expected to be created
    timeout_seconds: Optional[int] = None
    retry_count: int = 0
    max_retries: int = 3
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_info: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Apply config defaults after initialization."""
        from .. import config
        if self.timeout_seconds is None:
            self.timeout_seconds = config.MICRO_CHECKPOINT_TIMEOUT
        if self.max_retries == 3:  # Only override if using default
            self.max_retries = config.MICRO_CHECKPOINT_MAX_RETRIES

@dataclass
class OperationProgress:
    """Tracks progress through a multi-step operation."""
    operation_id: str
    agent_name: str
    total_steps: int
    completed_steps: List[str]
    current_step: Optional[str] = None
    failed_steps: List[str] = None
    operation_state: Dict[str, Any] = None
    created_at: str = None
    updated_at: str = None

    def __post_init__(self):
        if self.failed_steps is None:
            self.failed_steps = []
        if self.operation_state is None:
            self.operation_state = {}
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc).isoformat()
        self.updated_at = datetime.now(timezone.utc).isoformat()

class CheckpointManager:
    """Manages the lifecycle of checkpoints and resumable operations."""

    def __init__(self, task_id: str):
        self.task_id = task_id
        self.operation_registry: Dict[str, OperationProgress] = {}
        self.current_operation: Optional[str] = None

    @property
    def checkpoints_dir(self) -> str:
        """Get the base checkpoints directory for the current task."""
        path = config.get_checkpoints_dir(self.task_id)
        os.makedirs(path, exist_ok=True)
        return path

    @property
    def micro_checkpoints_dir(self) -> str:
        """Get the micro-checkpoints directory, ensuring it exists."""
        path = os.path.join(self.checkpoints_dir, "micro_checkpoints")
        os.makedirs(path, exist_ok=True)
        return path

    def start_operation(self, 
                       operation_id: str,
                       agent_name: str,
                       steps: List[OperationStep],
                       operation_state: Dict[str, Any] = None) -> Optional[str]:
        """Start tracking a multi-step operation."""
        if not config.ENABLE_MICRO_CHECKPOINTS:
            logger.warning("⚠️  Micro-checkpoints disabled in config")
            return None
        
        progress = OperationProgress(
            operation_id=operation_id,
            agent_name=agent_name,
            total_steps=len(steps),
            completed_steps=[],
            operation_state=operation_state or {}
        )
        
        operation_path = os.path.join(self.micro_checkpoints_dir, f"operation_{operation_id}.json")
        
        operation_data = {
            "progress": asdict(progress),
            "steps": [asdict(step) for step in steps],
            "checkpoints": []
        }
        
        with open(operation_path, 'w') as f:
            json.dump(operation_data, f, indent=2, default=str)
        
        self.operation_registry[operation_id] = progress
        self.current_operation = operation_id
        
        logger.info(f"🔍 Started micro-tracked operation: {operation_id} for agent {agent_name} with {len(steps)} steps.")
        return operation_id

    @contextmanager
    def step_context(self, step: OperationStep):
        """Context manager for executing a single step with automatic checkpointing."""
        if not self.current_operation:
            raise ValueError("No active operation - call start_operation() first")
        
        operation_id = self.current_operation
        step.started_at = datetime.now(timezone.utc).isoformat()
        
        logger.info(f"🔄 Executing step: {step.step_name}")
        
        try:
            self._create_step_checkpoint(operation_id, step, "pre_execution")
            yield step
            step.completed_at = datetime.now(timezone.utc).isoformat()
            self._mark_step_completed(operation_id, step.step_id)
            self._create_step_checkpoint(operation_id, step, "completed")
            logger.info(f"✅ Step completed: {step.step_name}")
        except Exception as e:
            step.error_info = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "retry_count": step.retry_count
            }
            self._create_step_checkpoint(operation_id, step, "failed")
            self._mark_step_failed(operation_id, step.step_id, step.error_info)
            logger.error(f"❌ Step failed: {step.step_name} - {e}")
            if step.retry_count < step.max_retries:
                step.retry_count += 1
                logger.warning(f"🔄 Retrying step (attempt {step.retry_count + 1}/{step.max_retries + 1})")
                raise
            else:
                logger.critical(f"💀 Step failed permanently after {step.max_retries} retries")
                raise

    def resume_operation(self, operation_id: str) -> Optional[OperationProgress]:
        """Resume a partially completed operation."""
        operation_path = os.path.join(self.micro_checkpoints_dir, f"operation_{operation_id}.json")
        if not os.path.exists(operation_path):
            logger.error(f"❌ Operation not found: {operation_id}")
            return None
        
        try:
            with open(operation_path, 'r') as f:
                operation_data = json.load(f)
            
            progress = OperationProgress(**operation_data["progress"])
            self.operation_registry[operation_id] = progress
            self.current_operation = operation_id
            
            logger.info(f"🔄 RESUMING MICRO-OPERATION: {operation_id}")
            return progress
        except Exception as e:
            logger.error(f"❌ Error resuming operation {operation_id}: {e}")
            return None

    def list_recoverable_operations(self) -> List[Dict[str, Any]]:
        """List operations that can be resumed."""
        operations = []
        if not os.path.exists(self.micro_checkpoints_dir):
            return operations
        
        for filename in os.listdir(self.micro_checkpoints_dir):
            if filename.startswith("operation_") and filename.endswith(".json"):
                try:
                    with open(os.path.join(self.micro_checkpoints_dir, filename), 'r') as f:
                        progress = json.load(f)["progress"]
                    if len(progress["completed_steps"]) < progress["total_steps"]:
                        operations.append({
                            "operation_id": progress["operation_id"],
                            "agent_name": progress["agent_name"],
                            "progress": f"{len(progress['completed_steps'])}/{progress['total_steps']}",
                            "failed_steps": len(progress.get("failed_steps", [])),
                            "created_at": progress["created_at"],
                            "current_step": progress.get("current_step")
                        })
                except Exception as e:
                    logger.warning(f"⚠️  Error reading operation {filename}: {e}")
        
        return sorted(operations, key=lambda x: x["created_at"], reverse=True)

    def save_state_snapshot(self, state: DOMISessionState, phase: str):
        """Save a complete snapshot of the application state and outputs."""
        timestamp = datetime.now(timezone.utc).isoformat().replace(":", "-").replace(".", "-")
        snapshot_name = f"snapshot_{phase}_{timestamp}"
        snapshot_dir = os.path.join(self.checkpoints_dir, snapshot_name)
        os.makedirs(snapshot_dir, exist_ok=True)

        state_path = os.path.join(snapshot_dir, "domi_state.json")
        with open(state_path, 'w') as f:
            json.dump(state.model_dump(), f, indent=2)

        outputs_dir = config.get_outputs_dir(self.task_id)
        if os.path.exists(outputs_dir):
            archive_path = os.path.join(snapshot_dir, "outputs_snapshot")
            shutil.make_archive(archive_path, 'zip', outputs_dir)
            logger.info(f"Saved and archived outputs to {archive_path}.zip")

        logger.info(f"[CheckpointManager]: Saved state snapshot to {snapshot_dir}")

    def load_latest_snapshot(self) -> Optional[DOMISessionState]:
        """Load the most recent state snapshot and restore outputs."""
        snapshots = self.get_sorted_snapshots()
        if not snapshots:
            return None

        latest_snapshot_dir = os.path.join(self.checkpoints_dir, snapshots[0])
        state_path = os.path.join(latest_snapshot_dir, "domi_state.json")
        archive_path = os.path.join(latest_snapshot_dir, "outputs_snapshot.zip")

        if os.path.exists(state_path):
            with open(state_path, 'r') as f:
                state = DOMISessionState(**json.load(f))
            
            if os.path.exists(archive_path):
                outputs_dir = config.get_outputs_dir(self.task_id)
                if os.path.exists(outputs_dir):
                    shutil.rmtree(outputs_dir)
                shutil.unpack_archive(archive_path, outputs_dir)
                logger.info(f"Restored outputs from {archive_path}")

            return state
        return None

    def has_snapshot(self) -> bool:
        """Check if any snapshots exist for the current task."""
        return bool(self.get_sorted_snapshots())

    def get_sorted_snapshots(self) -> List[str]:
        """Get a sorted list of all snapshots for the current task."""
        if not os.path.exists(self.checkpoints_dir):
            return []
        return sorted(
            [d for d in os.listdir(self.checkpoints_dir) if os.path.isdir(os.path.join(self.checkpoints_dir, d)) and d.startswith('snapshot_')],
            reverse=True
        )

    def _create_step_checkpoint(self, operation_id: str, step: OperationStep, phase: str):
        """Create a checkpoint for a specific step phase."""
        timestamp = datetime.now(timezone.utc).isoformat()
        checkpoint_id = f"step_{operation_id}_{step.step_id}_{phase}_{timestamp.replace(':', '-').replace('.', '-')}"
        
        checkpoint_data = {
            "checkpoint_id": checkpoint_id,
            "operation_id": operation_id,
            "step_id": step.step_id,
            "phase": phase,
            "timestamp": timestamp,
            "step_data": asdict(step),
            "operation_state": self.operation_registry[operation_id].operation_state
        }
        
        checkpoint_path = os.path.join(self.micro_checkpoints_dir, f"{checkpoint_id}.json")
        with open(checkpoint_path, 'w') as f:
            json.dump(checkpoint_data, f, indent=2, default=str)
        
        if config.VERBOSE_LOGGING:
            logger.debug(f"   💾 Micro-checkpoint: {checkpoint_id}")

    def _mark_step_completed(self, operation_id: str, step_id: str):
        """Mark a step as completed in the operation progress."""
        progress = self.operation_registry[operation_id]
        if step_id not in progress.completed_steps:
            progress.completed_steps.append(step_id)
        progress.updated_at = datetime.now(timezone.utc).isoformat()
        self._save_operation_progress(operation_id)

    def _mark_step_failed(self, operation_id: str, step_id: str, error_info: Dict[str, Any]):
        """Mark a step as failed in the operation progress."""
        progress = self.operation_registry[operation_id]
        if step_id not in progress.failed_steps:
            progress.failed_steps.append(step_id)
        progress.updated_at = datetime.now(timezone.utc).isoformat()
        self._save_operation_progress(operation_id)

    def _save_operation_progress(self, operation_id: str):
        """Save the current operation progress to disk."""
        operation_path = os.path.join(self.micro_checkpoints_dir, f"operation_{operation_id}.json")
        if os.path.exists(operation_path):
            with open(operation_path, 'r') as f:
                operation_data = json.load(f)
            operation_data["progress"] = asdict(self.operation_registry[operation_id])
            with open(operation_path, 'w') as f:
                json.dump(operation_data, f, indent=2, default=str)

    def mark_operation_complete(self, operation_id: str):
        """Mark an operation as complete and archive it."""
        if operation_id in self.operation_registry:
            del self.operation_registry[operation_id]
            if self.current_operation == operation_id:
                self.current_operation = None
            logger.info(f"✓ Marked operation complete: {operation_id}")
        
        # Instead of deleting, archive the operation file for history
        op_path = os.path.join(self.micro_checkpoints_dir, f"operation_{operation_id}.json")
        if os.path.exists(op_path):
            archive_dir = os.path.join(self.micro_checkpoints_dir, "completed")
            os.makedirs(archive_dir, exist_ok=True)
            shutil.move(op_path, os.path.join(archive_dir, f"operation_{operation_id}.json"))

# Global instance for convenience, though direct instantiation is preferred for multi-tasking
checkpoint_manager = CheckpointManager(config.TASK_ID)