# /department_of_market_intelligence/utils/checkpoint_manager.py
"""Checkpoint management system for research task recovery and resumption."""

import os
import json
import pickle
import shutil
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from pathlib import Path

from .. import config


class CheckpointManager:
    """Manages checkpoints for research task execution with recovery capabilities."""
    
    def __init__(self, task_id: str = None):
        self.task_id = task_id or config.TASK_ID
        self.checkpoints_dir = config.get_checkpoints_dir(self.task_id)
        self.outputs_dir = config.get_outputs_dir(self.task_id)
        
        # Ensure directories exist
        os.makedirs(self.checkpoints_dir, exist_ok=True)
        os.makedirs(self.outputs_dir, exist_ok=True)
        
        self.current_checkpoint = None
        self.agent_execution_count = 0
        
    def create_checkpoint(self, 
                         phase: str, 
                         step: str, 
                         session_state: Dict[str, Any],  # Simple dict following ADK patterns
                         metadata: Dict[str, Any] = None) -> str:
        """Create a new checkpoint with current state."""
        if not config.ENABLE_CHECKPOINTING:
            return None
            
        timestamp = datetime.now(timezone.utc).isoformat()
        checkpoint_id = f"{phase}_{step}_{timestamp.replace(':', '-').replace('.', '-')}"
        
        # Use simple dict state following ADK patterns
        if not isinstance(session_state, dict):
            raise ValueError("session_state must be a simple dict following ADK patterns")
        
        # Create a clean copy of state with only serializable values
        state_dict = {}
        for key, value in session_state.items():
            # Only store simple, serializable types
            if isinstance(value, (str, int, float, bool, list, dict, type(None))):
                state_dict[key] = value
            else:
                print(f"⚠️  Skipping non-serializable state key '{key}': {type(value)}")
        
        checkpoint_data = {
            "checkpoint_id": checkpoint_id,
            "task_id": self.task_id,
            "timestamp": timestamp,
            "phase": phase,
            "step": step,
            "session_state": state_dict,
            "metadata": metadata or {},
            "agent_execution_count": self.agent_execution_count,
            "uses_adk_patterns": True  # Mark as using proper ADK patterns
        }
        
        # Save checkpoint
        checkpoint_path = os.path.join(self.checkpoints_dir, f"{checkpoint_id}.json")
        with open(checkpoint_path, 'w') as f:
            json.dump(checkpoint_data, f, indent=2, default=str)
        
        # Create snapshot of outputs directory
        self._create_outputs_snapshot(checkpoint_id)
        
        # Update latest checkpoint pointer
        self._update_latest_checkpoint(checkpoint_id)
        
        print(f"💾 CHECKPOINT SAVED: {checkpoint_id}")
        if config.VERBOSE_LOGGING:
            print(f"   📁 Path: {checkpoint_path}")
            print(f"   📊 Using ADK patterns - Session keys: {list(state_dict.keys())}")
        
        self.current_checkpoint = checkpoint_id
        return checkpoint_id
    
    def load_checkpoint(self, checkpoint_id: str = None) -> Optional[Dict[str, Any]]:
        """Load a specific checkpoint or the latest one.
        
        Args:
            checkpoint_id: Specific checkpoint to load, or None for latest
            
        Returns:
            Checkpoint data dict with simple state following ADK patterns
        """
        if not config.ENABLE_CHECKPOINTING:
            return None
            
        if checkpoint_id is None:
            checkpoint_id = self._get_latest_checkpoint()
        
        if not checkpoint_id:
            print("📋 No checkpoints found for recovery")
            return None
        
        checkpoint_path = os.path.join(self.checkpoints_dir, f"{checkpoint_id}.json")
        
        if not os.path.exists(checkpoint_path):
            print(f"❌ Checkpoint not found: {checkpoint_id}")
            return None
        
        try:
            with open(checkpoint_path, 'r') as f:
                checkpoint_data = json.load(f)
            
            # Restore outputs snapshot
            self._restore_outputs_snapshot(checkpoint_id)
            
            print(f"🔄 CHECKPOINT LOADED: {checkpoint_id}")
            print(f"   📅 Created: {checkpoint_data['timestamp']}")
            print(f"   🎯 Phase: {checkpoint_data['phase']} → {checkpoint_data['step']}")
            print(f"   🔢 Agent executions: {checkpoint_data['agent_execution_count']}")
            
            # Check if this uses new ADK patterns or legacy format
            if checkpoint_data.get('uses_adk_patterns', False):
                print(f"   ✅ Using proper ADK state patterns")
            else:
                print(f"   ⚠️  Legacy checkpoint format - state may need migration")
            
            self.current_checkpoint = checkpoint_id
            self.agent_execution_count = checkpoint_data['agent_execution_count']
            
            return checkpoint_data
            
        except Exception as e:
            print(f"❌ Error loading checkpoint {checkpoint_id}: {e}")
            return None
    
    def list_checkpoints(self) -> List[Dict[str, Any]]:
        """List all available checkpoints for the current task."""
        checkpoints = []
        
        if not os.path.exists(self.checkpoints_dir):
            return checkpoints
        
        for filename in os.listdir(self.checkpoints_dir):
            if filename.endswith('.json') and not filename.startswith('latest_'):
                checkpoint_path = os.path.join(self.checkpoints_dir, filename)
                try:
                    with open(checkpoint_path, 'r') as f:
                        checkpoint_data = json.load(f)
                    
                    checkpoints.append({
                        "checkpoint_id": checkpoint_data["checkpoint_id"],
                        "timestamp": checkpoint_data["timestamp"],
                        "phase": checkpoint_data["phase"],
                        "step": checkpoint_data["step"],
                        "agent_count": checkpoint_data.get("agent_execution_count", 0)
                    })
                except Exception as e:
                    print(f"⚠️  Error reading checkpoint {filename}: {e}")
        
        # Sort by timestamp (newest first)
        checkpoints.sort(key=lambda x: x["timestamp"], reverse=True)
        return checkpoints
    
    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """Delete a specific checkpoint and its associated files."""
        checkpoint_path = os.path.join(self.checkpoints_dir, f"{checkpoint_id}.json")
        snapshot_path = os.path.join(self.checkpoints_dir, f"outputs_snapshot_{checkpoint_id}")
        
        try:
            if os.path.exists(checkpoint_path):
                os.remove(checkpoint_path)
            
            if os.path.exists(snapshot_path):
                shutil.rmtree(snapshot_path)
            
            print(f"🗑️  Checkpoint deleted: {checkpoint_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error deleting checkpoint {checkpoint_id}: {e}")
            return False
    
    def cleanup_old_checkpoints(self, keep_count: int = 10):
        """Keep only the N most recent checkpoints."""
        checkpoints = self.list_checkpoints()
        
        if len(checkpoints) <= keep_count:
            return
        
        old_checkpoints = checkpoints[keep_count:]
        deleted_count = 0
        
        for checkpoint in old_checkpoints:
            if self.delete_checkpoint(checkpoint["checkpoint_id"]):
                deleted_count += 1
        
        print(f"🧹 Cleaned up {deleted_count} old checkpoints (kept {keep_count} most recent)")
    
    def increment_agent_count(self):
        """Increment the agent execution counter."""
        self.agent_execution_count += 1
    
    def should_checkpoint(self) -> bool:
        """Determine if a checkpoint should be created based on interval."""
        if not config.ENABLE_CHECKPOINTING:
            return False
        return self.agent_execution_count % config.CHECKPOINT_INTERVAL == 0
    
    def get_recovery_info(self) -> Dict[str, Any]:
        """Get information about available recovery options."""
        checkpoints = self.list_checkpoints()
        latest = self._get_latest_checkpoint()
        
        return {
            "task_id": self.task_id,
            "checkpoints_available": len(checkpoints),
            "latest_checkpoint": latest,
            "checkpoints_dir": self.checkpoints_dir,
            "outputs_dir": self.outputs_dir,
            "can_resume": latest is not None
        }
    
    def _create_outputs_snapshot(self, checkpoint_id: str):
        """Create a snapshot of the outputs directory."""
        if not os.path.exists(self.outputs_dir):
            return
        
        snapshot_path = os.path.join(self.checkpoints_dir, f"outputs_snapshot_{checkpoint_id}")
        try:
            shutil.copytree(self.outputs_dir, snapshot_path, dirs_exist_ok=True)
        except Exception as e:
            print(f"⚠️  Warning: Could not create outputs snapshot: {e}")
    
    def _restore_outputs_snapshot(self, checkpoint_id: str):
        """Restore outputs directory from snapshot."""
        snapshot_path = os.path.join(self.checkpoints_dir, f"outputs_snapshot_{checkpoint_id}")
        
        if not os.path.exists(snapshot_path):
            print(f"⚠️  Warning: No outputs snapshot found for {checkpoint_id}")
            return
        
        try:
            # Clear current outputs
            if os.path.exists(self.outputs_dir):
                shutil.rmtree(self.outputs_dir)
            
            # Restore from snapshot
            shutil.copytree(snapshot_path, self.outputs_dir)
            print(f"📂 Outputs restored from checkpoint snapshot")
            
        except Exception as e:
            print(f"❌ Error restoring outputs snapshot: {e}")
    
    def _update_latest_checkpoint(self, checkpoint_id: str):
        """Update the pointer to the latest checkpoint."""
        latest_path = os.path.join(self.checkpoints_dir, "latest_checkpoint.txt")
        with open(latest_path, 'w') as f:
            f.write(checkpoint_id)
    
    def _get_latest_checkpoint(self) -> Optional[str]:
        """Get the ID of the latest checkpoint."""
        latest_path = os.path.join(self.checkpoints_dir, "latest_checkpoint.txt")
        
        if not os.path.exists(latest_path):
            return None
        
        try:
            with open(latest_path, 'r') as f:
                checkpoint_id = f.read().strip()
            
            # Verify the checkpoint file exists
            checkpoint_path = os.path.join(self.checkpoints_dir, f"{checkpoint_id}.json")
            if os.path.exists(checkpoint_path):
                return checkpoint_id
            else:
                return None
                
        except Exception:
            return None


# Global checkpoint manager instance
checkpoint_manager = CheckpointManager()