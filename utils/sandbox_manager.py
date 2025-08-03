# /department_of_market_intelligence/utils/sandbox_manager.py
"""
Sandbox manager for safe isolated execution of DoMI workflows.
"""

import os
import shutil
import tempfile
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path
import json
import atexit

from .. import config


class SandboxManager:
    """Manages isolated sandbox environments for safe workflow execution."""
    
    def __init__(self, session_id: Optional[str] = None):
        """Initialize sandbox manager.
        
        Args:
            session_id: Optional session identifier. If None, generates timestamp-based ID.
        """
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        self.sandbox_root = os.path.join(config.SANDBOX_BASE_DIR, f"session_{self.session_id}")
        self.initialized = False
        self.metadata = {
            "session_id": self.session_id,
            "created_at": datetime.now().isoformat(),
            "execution_mode": config.EXECUTION_MODE,
            "task_id": config.TASK_ID,
            "cleanup_enabled": config.AUTO_CLEANUP_SANDBOX
        }
        
        # Register cleanup if auto-cleanup is enabled
        if config.AUTO_CLEANUP_SANDBOX:
            atexit.register(self.cleanup)
    
    def initialize(self) -> str:
        """Initialize the sandbox environment.
        
        Returns:
            Path to the sandbox root directory
        """
        if self.initialized:
            return self.sandbox_root
        
        print(f"🏗️  Initializing sandbox environment: {self.session_id}")
        
        # Create sandbox directory structure
        os.makedirs(self.sandbox_root, exist_ok=True)
        
        # Create standard subdirectories
        subdirs = [
            "outputs",
            "checkpoints", 
            "logs",
            "temp",
            "workspace"
        ]
        
        for subdir in subdirs:
            os.makedirs(os.path.join(self.sandbox_root, subdir), exist_ok=True)
        
        # Copy task files to sandbox for reference
        self._copy_task_files()
        
        # Create metadata file
        self._write_metadata()
        
        # Log sandbox initialization
        self._log_initialization()
        
        self.initialized = True
        return self.sandbox_root
    
    def get_sandbox_path(self, relative_path: str = "") -> str:
        """Get absolute path within sandbox.
        
        Args:
            relative_path: Path relative to sandbox root
            
        Returns:
            Absolute path within sandbox
        """
        if not self.initialized:
            self.initialize()
        
        return os.path.join(self.sandbox_root, relative_path)
    
    def get_outputs_dir(self, task_id: Optional[str] = None) -> str:
        """Get sandbox outputs directory for a task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Path to task outputs directory in sandbox
        """
        task_id = task_id or config.TASK_ID
        return self.get_sandbox_path(f"outputs/{task_id}")
    
    def get_checkpoints_dir(self, task_id: Optional[str] = None) -> str:
        """Get sandbox checkpoints directory for a task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Path to task checkpoints directory in sandbox
        """
        task_id = task_id or config.TASK_ID
        return self.get_sandbox_path(f"checkpoints/{task_id}")
    
    def create_directory_structure(self, task_id: Optional[str] = None) -> None:
        """Create complete directory structure for a task in sandbox.
        
        Args:
            task_id: Task identifier
        """
        task_id = task_id or config.TASK_ID
        outputs_dir = self.get_outputs_dir(task_id)
        
        # Create the same structure as production but in sandbox
        from .directory_manager import create_task_directory_structure
        
        create_task_directory_structure(outputs_dir)
        
        print(f"📁 Created sandbox directory structure for task: {task_id}")
        print(f"   📍 Location: {outputs_dir}")
    
    def copy_from_production(self, source_path: str, dest_path: str) -> bool:
        """Copy files from production environment to sandbox.
        
        Args:
            source_path: Source path in production environment
            dest_path: Destination path in sandbox (relative to sandbox root)
            
        Returns:
            True if copy succeeded, False otherwise
        """
        try:
            full_source = source_path
            full_dest = self.get_sandbox_path(dest_path)
            
            # Create destination directory if needed
            os.makedirs(os.path.dirname(full_dest), exist_ok=True)
            
            if os.path.isfile(full_source):
                shutil.copy2(full_source, full_dest)
            elif os.path.isdir(full_source):
                shutil.copytree(full_source, full_dest, dirs_exist_ok=True)
            else:
                print(f"⚠️  Source path does not exist: {full_source}")
                return False
            
            print(f"📄 Copied to sandbox: {dest_path}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to copy to sandbox: {e}")
            return False
    
    def export_to_production(self, source_path: str, dest_path: str, 
                           confirm: bool = True) -> bool:
        """Export files from sandbox to production environment.
        
        Args:
            source_path: Source path in sandbox (relative to sandbox root)
            dest_path: Destination path in production environment
            confirm: Whether to require confirmation
            
        Returns:
            True if export succeeded, False otherwise
        """
        if config.EXECUTION_MODE != "production" and confirm:
            response = input(f"⚠️  Export {source_path} to production? (y/N): ")
            if response.lower() != 'y':
                print("❌ Export cancelled")
                return False
        
        try:
            full_source = self.get_sandbox_path(source_path)
            full_dest = dest_path
            
            if not os.path.exists(full_source):
                print(f"❌ Source path does not exist in sandbox: {source_path}")
                return False
            
            # Create destination directory if needed
            os.makedirs(os.path.dirname(full_dest), exist_ok=True)
            
            # Create backup if enabled
            if config.PRODUCTION_BACKUP_ENABLED and os.path.exists(full_dest):
                backup_path = f"{full_dest}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copy2(full_dest, backup_path)
                print(f"💾 Created backup: {backup_path}")
            
            if os.path.isfile(full_source):
                shutil.copy2(full_source, full_dest)
            elif os.path.isdir(full_source):
                shutil.copytree(full_source, full_dest, dirs_exist_ok=True)
            
            print(f"📤 Exported to production: {dest_path}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to export to production: {e}")
            return False
    
    def list_contents(self) -> Dict[str, Any]:
        """List contents of the sandbox.
        
        Returns:
            Dictionary with sandbox contents information
        """
        if not self.initialized:
            return {"error": "Sandbox not initialized"}
        
        contents = {"directories": [], "files": [], "total_size": 0}
        
        for root, dirs, files in os.walk(self.sandbox_root):
            rel_root = os.path.relpath(root, self.sandbox_root)
            if rel_root != ".":
                contents["directories"].append(rel_root)
            
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, self.sandbox_root)
                file_size = os.path.getsize(file_path)
                contents["files"].append({
                    "path": rel_path,
                    "size": file_size,
                    "modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                })
                contents["total_size"] += file_size
        
        return contents
    
    def cleanup(self) -> bool:
        """Clean up the sandbox environment.
        
        Returns:
            True if cleanup succeeded, False otherwise
        """
        if not os.path.exists(self.sandbox_root):
            return True
        
        try:
            # Preserve logs if configured
            if config.SANDBOX_PRESERVE_LOGS:
                logs_backup_dir = os.path.join(config.SANDBOX_BASE_DIR, "logs", self.session_id)
                logs_dir = os.path.join(self.sandbox_root, "logs")
                if os.path.exists(logs_dir):
                    os.makedirs(os.path.dirname(logs_backup_dir), exist_ok=True)
                    shutil.copytree(logs_dir, logs_backup_dir, dirs_exist_ok=True)
                    print(f"💾 Preserved logs: {logs_backup_dir}")
            
            # Remove sandbox directory
            shutil.rmtree(self.sandbox_root)
            print(f"🧹 Cleaned up sandbox: {self.session_id}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to clean up sandbox: {e}")
            return False
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of sandbox session.
        
        Returns:
            Dictionary with sandbox session summary
        """
        summary = self.metadata.copy()
        
        if self.initialized:
            contents = self.list_contents()
            summary.update({
                "sandbox_path": self.sandbox_root,
                "file_count": len(contents["files"]),
                "directory_count": len(contents["directories"]),
                "total_size_mb": round(contents["total_size"] / 1024 / 1024, 2),
                "status": "active"
            })
        else:
            summary["status"] = "not_initialized"
        
        return summary
    
    def _copy_task_files(self) -> None:
        """Copy task files to sandbox for reference."""
        try:
            # Copy task description - Use direct path construction to avoid recursion
            source_task = os.path.join(config.TASKS_DIR, f"{config.TASK_ID}.md")
            if os.path.exists(source_task):
                dest_task = os.path.join(self.sandbox_root, f"tasks/{config.TASK_ID}.md")
                os.makedirs(os.path.dirname(dest_task), exist_ok=True)
                shutil.copy2(source_task, dest_task)
        except Exception as e:
            print(f"⚠️  Failed to copy task files: {e}")
    
    def _write_metadata(self) -> None:
        """Write sandbox metadata file."""
        try:
            # Use direct path construction to avoid recursion
            metadata_path = os.path.join(self.sandbox_root, "sandbox_metadata.json")
            with open(metadata_path, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            print(f"⚠️  Failed to write sandbox metadata: {e}")
    
    def _log_initialization(self) -> None:
        """Log sandbox initialization details."""
        # Use direct path construction to avoid recursion
        log_path = os.path.join(self.sandbox_root, "logs/sandbox_init.log")
        try:
            with open(log_path, 'w') as f:
                f.write(f"Sandbox Session: {self.session_id}\n")
                f.write(f"Created: {self.metadata['created_at']}\n")
                f.write(f"Execution Mode: {config.EXECUTION_MODE}\n")
                f.write(f"Task ID: {config.TASK_ID}\n")
                f.write(f"Sandbox Path: {self.sandbox_root}\n")
                f.write(f"Auto Cleanup: {config.AUTO_CLEANUP_SANDBOX}\n")
                f.write(f"Preserve Logs: {config.SANDBOX_PRESERVE_LOGS}\n")
        except Exception as e:
            print(f"⚠️  Failed to write initialization log: {e}")


# Global sandbox instance
_sandbox_instance: Optional[SandboxManager] = None


def get_sandbox_manager() -> SandboxManager:
    """Get or create the global sandbox manager instance.
    
    Returns:
        SandboxManager instance
    """
    global _sandbox_instance
    
    if _sandbox_instance is None:
        _sandbox_instance = SandboxManager()
    
    return _sandbox_instance


def initialize_sandbox() -> str:
    """Initialize the sandbox environment.
    
    Returns:
        Path to sandbox root directory
    """
    manager = get_sandbox_manager()
    return manager.initialize()


def cleanup_sandbox() -> bool:
    """Clean up the current sandbox environment.
    
    Returns:
        True if cleanup succeeded
    """
    global _sandbox_instance
    
    if _sandbox_instance:
        success = _sandbox_instance.cleanup()
        _sandbox_instance = None
        return success
    
    return True


def is_sandbox_mode() -> bool:
    """Check if currently running in sandbox mode.
    
    Returns:
        True if in sandbox mode
    """
    return config.EXECUTION_MODE == "sandbox"


def validate_sandbox_safety() -> bool:
    """Validate that sandbox configuration is safe.
    
    Returns:
        True if sandbox configuration is safe
    """
    if not is_sandbox_mode():
        return True
    
    # Note: Sandbox mode now uses project directories for real output generation
    # Safety is provided through execution monitoring, not directory isolation
    print("✅ Sandbox mode: Using project directories for real output generation")
    print(f"   📁 Project directory: {config._BASE_DIR}")
    print(f"   📊 Outputs directory: {config.get_outputs_dir()}")
    
    # Check that project outputs directory exists and is writable
    outputs_dir = config.get_outputs_dir()
    if not os.path.exists(outputs_dir):
        try:
            os.makedirs(outputs_dir, exist_ok=True)
            print(f"✅ Created outputs directory: {outputs_dir}")
        except Exception as e:
            print(f"❌ Cannot create outputs directory: {e}")
            return False
    
    if not os.access(outputs_dir, os.W_OK):
        print(f"❌ Outputs directory is not writable: {outputs_dir}")
        return False
    
    return True