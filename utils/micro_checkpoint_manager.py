# /department_of_market_intelligence/utils/micro_checkpoint_manager.py
"""Micro-checkpoint system for fine-grained operation recovery."""

import os
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from contextlib import contextmanager

from .. import config
from .checkpoint_manager import checkpoint_manager


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


class MicroCheckpointManager:
    """Manages fine-grained checkpoints for individual operations."""
    
    def __init__(self, task_id: str = None):
        self.task_id = task_id or config.TASK_ID
        self.micro_checkpoints_dir = os.path.join(
            config.get_checkpoints_dir(self.task_id), 
            "micro_checkpoints"
        )
        os.makedirs(self.micro_checkpoints_dir, exist_ok=True)
        
        self.operation_registry: Dict[str, OperationProgress] = {}
        self.current_operation: Optional[str] = None
        
    def start_operation(self, 
                       operation_id: str,
                       agent_name: str,
                       steps: List[OperationStep],
                       operation_state: Dict[str, Any] = None) -> str:
        """Start tracking a multi-step operation."""
        
        progress = OperationProgress(
            operation_id=operation_id,
            agent_name=agent_name,
            total_steps=len(steps),
            completed_steps=[],
            operation_state=operation_state or {}
        )
        
        # Save operation metadata
        operation_path = os.path.join(
            self.micro_checkpoints_dir, 
            f"operation_{operation_id}.json"
        )
        
        operation_data = {
            "progress": asdict(progress),
            "steps": [asdict(step) for step in steps],
            "checkpoints": []
        }
        
        with open(operation_path, 'w') as f:
            json.dump(operation_data, f, indent=2, default=str)
        
        self.operation_registry[operation_id] = progress
        self.current_operation = operation_id
        
        print(f"🔍 Started micro-tracked operation: {operation_id}")
        print(f"   📊 Agent: {agent_name}")
        print(f"   🎯 Steps: {len(steps)}")
        
        return operation_id
    
    @contextmanager
    def step_context(self, step: OperationStep):
        """Context manager for executing a single step with automatic checkpointing."""
        if not self.current_operation:
            raise ValueError("No active operation - call start_operation() first")
        
        operation_id = self.current_operation
        step.started_at = datetime.now(timezone.utc).isoformat()
        
        print(f"🔄 Executing step: {step.step_name}")
        
        try:
            # Create pre-execution checkpoint
            self._create_step_checkpoint(operation_id, step, "pre_execution")
            
            yield step
            
            # Mark step as completed
            step.completed_at = datetime.now(timezone.utc).isoformat()
            self._mark_step_completed(operation_id, step.step_id)
            
            # Create post-execution checkpoint
            self._create_step_checkpoint(operation_id, step, "completed")
            
            print(f"✅ Step completed: {step.step_name}")
            
        except Exception as e:
            # Capture error context
            step.error_info = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "retry_count": step.retry_count
            }
            
            # Create error checkpoint
            self._create_step_checkpoint(operation_id, step, "failed")
            
            self._mark_step_failed(operation_id, step.step_id, step.error_info)
            
            print(f"❌ Step failed: {step.step_name} - {e}")
            
            # Check if we should retry
            if step.retry_count < step.max_retries:
                step.retry_count += 1
                print(f"🔄 Retrying step (attempt {step.retry_count + 1}/{step.max_retries + 1})")
                # Re-raise to trigger retry logic
                raise
            else:
                print(f"💀 Step failed permanently after {step.max_retries} retries")
                raise
    
    def resume_operation(self, operation_id: str) -> Optional[OperationProgress]:
        """Resume a partially completed operation."""
        operation_path = os.path.join(
            self.micro_checkpoints_dir,
            f"operation_{operation_id}.json"
        )
        
        if not os.path.exists(operation_path):
            print(f"❌ Operation not found: {operation_id}")
            return None
        
        try:
            with open(operation_path, 'r') as f:
                operation_data = json.load(f)
            
            progress_data = operation_data["progress"]
            progress = OperationProgress(**progress_data)
            
            steps_data = operation_data["steps"]
            steps = [OperationStep(**step_data) for step_data in steps_data]
            
            self.operation_registry[operation_id] = progress
            self.current_operation = operation_id
            
            remaining_steps = [
                step for step in steps 
                if step.step_id not in progress.completed_steps
                and step.step_id not in progress.failed_steps
            ]
            
            print(f"🔄 RESUMING MICRO-OPERATION: {operation_id}")
            print(f"   ✅ Completed: {len(progress.completed_steps)}/{progress.total_steps}")
            print(f"   ❌ Failed: {len(progress.failed_steps)}")
            print(f"   🔄 Remaining: {len(remaining_steps)}")
            
            return progress
            
        except Exception as e:
            print(f"❌ Error resuming operation {operation_id}: {e}")
            return None
    
    def list_recoverable_operations(self) -> List[Dict[str, Any]]:
        """List operations that can be resumed."""
        operations = []
        
        if not os.path.exists(self.micro_checkpoints_dir):
            return operations
        
        for filename in os.listdir(self.micro_checkpoints_dir):
            if filename.startswith("operation_") and filename.endswith(".json"):
                operation_path = os.path.join(self.micro_checkpoints_dir, filename)
                
                try:
                    with open(operation_path, 'r') as f:
                        operation_data = json.load(f)
                    
                    progress = operation_data["progress"]
                    
                    # Only include operations that are not fully complete
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
                    print(f"⚠️  Error reading operation {filename}: {e}")
        
        # Sort by creation time (newest first)
        operations.sort(key=lambda x: x["created_at"], reverse=True)
        return operations
    
    def get_step_checkpoints(self, operation_id: str, step_id: str) -> List[Dict[str, Any]]:
        """Get all checkpoints for a specific step."""
        step_checkpoints = []
        
        checkpoint_pattern = f"step_{operation_id}_{step_id}_"
        
        for filename in os.listdir(self.micro_checkpoints_dir):
            if filename.startswith(checkpoint_pattern) and filename.endswith(".json"):
                checkpoint_path = os.path.join(self.micro_checkpoints_dir, filename)
                
                try:
                    with open(checkpoint_path, 'r') as f:
                        checkpoint_data = json.load(f)
                    step_checkpoints.append(checkpoint_data)
                except Exception as e:
                    print(f"⚠️  Error reading checkpoint {filename}: {e}")
        
        return sorted(step_checkpoints, key=lambda x: x["timestamp"])
    
    def cleanup_completed_operations(self, keep_days: int = 7):
        """Clean up checkpoints for completed operations older than keep_days."""
        cutoff_time = time.time() - (keep_days * 24 * 60 * 60)
        
        if not os.path.exists(self.micro_checkpoints_dir):
            return
        
        cleaned_count = 0
        
        for filename in os.listdir(self.micro_checkpoints_dir):
            file_path = os.path.join(self.micro_checkpoints_dir, filename)
            
            try:
                file_stat = os.stat(file_path)
                
                if file_stat.st_mtime < cutoff_time:
                    # Check if this is a completed operation
                    if filename.startswith("operation_"):
                        with open(file_path, 'r') as f:
                            operation_data = json.load(f)
                        
                        progress = operation_data["progress"]
                        if len(progress["completed_steps"]) >= progress["total_steps"]:
                            os.remove(file_path)
                            cleaned_count += 1
                    
                    # Clean up associated step checkpoints
                    elif filename.startswith("step_"):
                        os.remove(file_path)
                        cleaned_count += 1
                        
            except Exception as e:
                print(f"⚠️  Error cleaning {filename}: {e}")
        
        if cleaned_count > 0:
            print(f"🧹 Cleaned up {cleaned_count} old micro-checkpoints")
    
    def _create_step_checkpoint(self, operation_id: str, step: OperationStep, phase: str):
        """Create a checkpoint for a specific step phase."""
        timestamp = datetime.now(timezone.utc).isoformat()
        checkpoint_id = f"step_{operation_id}_{step.step_id}_{phase}_{timestamp.replace(':', '-').replace('.', '-')}"
        
        checkpoint_data = {
            "checkpoint_id": checkpoint_id,
            "operation_id": operation_id,
            "step_id": step.step_id,
            "phase": phase,  # "pre_execution", "completed", "failed"
            "timestamp": timestamp,
            "step_data": asdict(step),
            "operation_state": self.operation_registry[operation_id].operation_state
        }
        
        checkpoint_path = os.path.join(
            self.micro_checkpoints_dir,
            f"{checkpoint_id}.json"
        )
        
        with open(checkpoint_path, 'w') as f:
            json.dump(checkpoint_data, f, indent=2, default=str)
        
        if config.VERBOSE_LOGGING:
            print(f"   💾 Micro-checkpoint: {checkpoint_id}")
    
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
        operation_path = os.path.join(
            self.micro_checkpoints_dir,
            f"operation_{operation_id}.json"
        )
        
        if os.path.exists(operation_path):
            with open(operation_path, 'r') as f:
                operation_data = json.load(f)
            
            operation_data["progress"] = asdict(self.operation_registry[operation_id])
            
            with open(operation_path, 'w') as f:
                json.dump(operation_data, f, indent=2, default=str)


# Global micro-checkpoint manager instance
micro_checkpoint_manager = MicroCheckpointManager()