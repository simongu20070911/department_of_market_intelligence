from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

class ValidationInfo(BaseModel):
    """Structured model for validation state."""
    validation_status: str = "pending"
    validation_context: str = "research_plan"
    validation_version: int = 0
    artifact_to_validate: Optional[str] = None
    plan_artifact_name: Optional[str] = None
    revision_reason: Optional[str] = None
    parallel_validation_issues_count: int = 0
    consolidated_validation_issues: List[str] = Field(default_factory=list)

class ExecutionInfo(BaseModel):
    """Structured model for execution state."""
    execution_status: str = "pending"
    execution_log_artifact: Optional[str] = None
    final_results_artifact: Optional[str] = None
    implementation_manifest_artifact: Optional[str] = None
    results_extraction_script_artifact: Optional[str] = None
    final_report_artifact: Optional[str] = None
    coder_subtask: Optional[Dict[str, Any]] = None
    
class DOMISessionState(BaseModel):
    """The structured session state for the DOMI workflow."""
    task_id: str
    current_phase: str = "research_planning"
    current_task_description: str = "Initial research planning"
    
    validation: ValidationInfo = Field(default_factory=ValidationInfo)
    execution: ExecutionInfo = Field(default_factory=ExecutionInfo)
    
    # For metadata and other unstructured data
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_checkpoint_dict(self) -> Dict[str, Any]:
        """Converts the Pydantic model to a dictionary suitable for checkpointing."""
        return self.model_dump(mode="json")

    @classmethod
    def from_checkpoint_dict(cls, data: Dict[str, Any]) -> "DOMISessionState":
        """Creates a DOMISessionState object from a dictionary."""
        return cls.model_validate(data)
