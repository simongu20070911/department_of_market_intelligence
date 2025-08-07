from .state_model import DOMISessionState, ValidationInfo, ExecutionInfo
from google.adk.agents.invocation_context import InvocationContext

def get_domi_state(ctx: InvocationContext) -> DOMISessionState:
    """
    Gets the structured DOMISessionState from the context, converting it if necessary.
    """
    if isinstance(ctx.session.state, DOMISessionState):
        return ctx.session.state
    
    # Convert from old dict-based state to new Pydantic model
    old_state = ctx.session.state or {}
    
    # Extract validation and execution info from old state
    validation_data = {
        "validation_status": old_state.get("domi_validation_status", "pending"),
        "validation_context": old_state.get("domi_validation_context", "research_plan"),
        "validation_version": old_state.get("domi_validation_version", 0),
        "artifact_to_validate": old_state.get("domi_artifact_to_validate"),
        "plan_artifact_name": old_state.get("domi_plan_artifact_name"),
        "revision_reason": old_state.get("domi_revision_reason"),
        "parallel_validation_issues_count": old_state.get("domi_parallel_validation_issues_count", 0),
        "consolidated_validation_issues": old_state.get("domi_consolidated_validation_issues", []),
    }
    
    execution_data = {
        "execution_status": old_state.get("domi_execution_status", "pending"),
        "execution_log_artifact": old_state.get("domi_execution_log_artifact"),
        "final_results_artifact": old_state.get("domi_final_results_artifact"),
        "implementation_manifest_artifact": old_state.get("domi_implementation_manifest_artifact"),
        "results_extraction_script_artifact": old_state.get("domi_results_extraction_script_artifact"),
        "final_report_artifact": old_state.get("domi_final_report_artifact"),
        "coder_subtask": old_state.get("domi_coder_subtask"),
    }
    
    new_state = DOMISessionState(
        task_id=old_state.get("domi_task_id", old_state.get("task_id")),
        current_phase=old_state.get("domi_current_phase", "research_planning"),
        current_task_description=old_state.get("domi_current_task", "Initial research planning"),
        validation=ValidationInfo(**validation_data),
        execution=ExecutionInfo(**execution_data),
        metadata=old_state.get("metadata", {})
    )
    
    ctx.session.state = new_state
    return new_state

def transition_to_next_phase(domi_state: DOMISessionState) -> bool:
    """
    Transitions the workflow to the next phase if the transition is valid.
    Returns True if the transition was successful, False otherwise.
    """
    from .phase_manager import WorkflowPhase, enhanced_phase_manager
    
    current_phase_str = domi_state.current_phase
    current_phase = WorkflowPhase.from_string(current_phase_str)
    
    if not current_phase:
        print(f"⚠️  Invalid current phase '{current_phase_str}' in state. Cannot transition.")
        return False
        
    phase_config = enhanced_phase_manager.get_phase_config(current_phase)
    if not phase_config or not phase_config.next_phases:
        print(f"⚠️  No next phase defined for '{current_phase_str}'. Cannot transition.")
        return False
        
    next_phase = phase_config.next_phases[0]
    
    if enhanced_phase_manager.can_transition(current_phase, next_phase):
        print(f"🔄 Transitioning from {current_phase.value} to {next_phase.value}")
        domi_state.current_phase = next_phase.value
        return True
    else:
        print(f"❌ Invalid transition attempted from {current_phase.value} to {next_phase.value}")
        return False
