# /department_of_market_intelligence/utils/state_model.py
"""
Pydantic SessionState model for type-safe state management.
Follows the Artifact-Pointer Pattern: stores file paths, not large data.
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime
import os


class TaskInfo(BaseModel):
    """Information about a coding or analysis task."""
    task_id: str
    description: str
    dependencies: List[str] = Field(default_factory=list)
    status: Literal["pending", "in_progress", "completed", "failed"] = "pending"
    output_artifact: Optional[str] = None  # File path to task output
    error_message: Optional[str] = None


class ValidationInfo(BaseModel):
    """Information about validation state."""
    validation_version: int = 0
    validation_status: Literal[
        "pending", 
        "approved", 
        "rejected", 
        "critical_error",
        "needs_revision",
        "needs_revision_after_junior_senior_validation",
        "needs_revision_after_parallel_validation",
        "approved_with_fallback"
    ] = "pending"
    revision_reason: Optional[str] = None  # Tracks why revision is needed
    parallel_validation_issues_count: int = 0  # Count of parallel validation issues
    junior_critique_artifact: Optional[str] = None  # File path
    senior_critique_artifact: Optional[str] = None  # File path
    parallel_validation_critical_issues: List[str] = Field(default_factory=list)
    consolidated_validation_issues: List[str] = Field(default_factory=list)


class ExecutionInfo(BaseModel):
    """Information about execution state."""
    execution_status: Literal["pending", "running", "success", "critical_error"] = "pending"
    error_type: Optional[str] = None
    error_details: Optional[str] = None
    suggested_fix: Optional[str] = None
    execution_log_artifact: Optional[str] = None  # File path to execution logs
    
    @field_validator('execution_log_artifact')
    @classmethod  
    def validate_execution_log_path(cls, v: Optional[str]) -> Optional[str]:
        """Ensure execution log path is valid when set."""
        if v is not None and not v.strip():
            raise ValueError("Execution log path cannot be empty string")
        return v


class SessionState(BaseModel):
    """Main session state model for the research framework.
    
    This model enforces type safety and follows the Artifact-Pointer Pattern:
    - Large data (research plans, code, results) are stored as file paths
    - Only lightweight metadata and control flow state is stored directly
    """
    
    # Task identification
    task_id: str = Field(description="Unique identifier for the research task")
    current_date: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    
    # Task input file
    task_file_path: Optional[str] = Field(
        default=None,
        description="Path to the original task description markdown file"
    )
    
    # Workflow phase tracking
    current_phase: Literal[
        "planning", 
        "implementation", 
        "execution", 
        "results_extraction", 
        "final_report"
    ] = "planning"
    current_task: Optional[str] = Field(
        default=None, 
        description="Current sub-task being executed"
    )
    
    # Research planning artifacts (file paths only)
    plan_artifact_name: Optional[str] = Field(
        default=None,
        description="Path to current research plan markdown file"
    )
    plan_version: int = Field(
        default=0,
        description="Version number of the research plan"
    )
    
    # Implementation artifacts (file paths only)
    implementation_manifest_artifact: Optional[str] = Field(
        default=None,
        description="Path to implementation manifest JSON"
    )
    results_extraction_script_artifact: Optional[str] = Field(
        default=None,
        description="Path to results extraction script"
    )
    
    # Validation state
    artifact_to_validate: Optional[str] = Field(
        default=None,
        description="Path to artifact currently being validated"
    )
    validation_info: ValidationInfo = Field(
        default_factory=ValidationInfo,
        description="Current validation state"
    )
    
    # Execution state
    execution_info: ExecutionInfo = Field(
        default_factory=ExecutionInfo,
        description="Current execution state"
    )
    
    # Coding tasks for parallel execution
    coder_subtask: Optional[TaskInfo] = Field(
        default=None,
        description="Current coding task being executed"
    )
    all_coding_tasks: List[TaskInfo] = Field(
        default_factory=list,
        description="All coding tasks from manifest"
    )
    
    # Final outputs (file paths only)
    final_report_artifact: Optional[str] = Field(
        default=None,
        description="Path to final research report"
    )
    final_results_artifact: Optional[str] = Field(
        default=None,
        description="Path to final results/data files"
    )
    
    # Checkpoint metadata
    last_checkpoint_time: Optional[datetime] = None
    checkpoint_version: int = 0
    
    # Additional metadata (small data only)
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional small metadata - no large data!"
    )
    
    @field_validator('metadata')
    @classmethod
    def validate_metadata_size(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure metadata doesn't contain large data."""
        # Simple size check - could be more sophisticated
        import json
        metadata_str = json.dumps(v)
        if len(metadata_str) > 10000:  # 10KB limit
            raise ValueError(
                "Metadata too large! Use file paths instead of storing data directly."
            )
        return v
    
    @field_validator('task_file_path', 'plan_artifact_name', 'implementation_manifest_artifact', 
                     'results_extraction_script_artifact', 'final_report_artifact',
                     'final_results_artifact')
    @classmethod
    def validate_artifact_paths(cls, v: Optional[str]) -> Optional[str]:
        """Ensure artifact paths are valid when set."""
        if v is not None and not v.strip():
            raise ValueError("Artifact path cannot be empty string")
        return v
    
    def get_validation_status(self) -> str:
        """Convenience method to get current validation status."""
        return self.validation_info.validation_status
    
    def set_validation_status(self, status: str) -> None:
        """Convenience method to set validation status with type checking."""
        self.validation_info.validation_status = status
    
    def get_execution_status(self) -> str:
        """Convenience method to get current execution status."""
        return self.execution_info.execution_status
    
    def set_execution_status(self, status: str) -> None:
        """Convenience method to set execution status with type checking."""
        self.execution_info.execution_status = status
    
    def increment_validation_version(self) -> None:
        """Increment the validation version counter."""
        self.validation_info.validation_version += 1
    
    def add_coding_task(self, task: TaskInfo) -> None:
        """Add a coding task to the list."""
        self.all_coding_tasks.append(task)
    
    def get_coding_task_by_id(self, task_id: str) -> Optional[TaskInfo]:
        """Get a coding task by its ID."""
        for task in self.all_coding_tasks:
            if task.task_id == task_id:
                return task
        return None
    
    def to_checkpoint_dict(self) -> dict:
        """Convert to dictionary for checkpoint saving."""
        return self.model_dump(mode='json')
    
    @classmethod
    def from_checkpoint_dict(cls, data: dict) -> 'SessionState':
        """Create SessionState from checkpoint dictionary."""
        return cls.model_validate(data)
    
    model_config = ConfigDict(
        validate_assignment=True,  # Validate on attribute assignment
        extra="forbid"  # Don't allow extra fields
    )