from .state_model import DOMISessionState
from google.adk.agents.invocation_context import InvocationContext
from .logger import get_logger

logger = get_logger(__name__)

def get_domi_state(ctx: InvocationContext) -> DOMISessionState:
    """
    Ensures the session state is a DOMISessionState object, initializing if necessary.
    """
    if not isinstance(ctx.session.state, DOMISessionState):
        logger.warning("Session state is not a DOMISessionState object. Initializing a new one.")
        from .. import config
        ctx.session.state = DOMISessionState(task_id=config.TASK_ID)
    return ctx.session.state

def update_session_state(ctx: InvocationContext, **kwargs):
    """
    Updates the session state in a structured way.
    """
    state = get_domi_state(ctx)
    for key, value in kwargs.items():
        if hasattr(state, key):
            setattr(state, key, value)
        else:
            logger.warning(f"Attempted to set unknown attribute '{key}' on DOMISessionState.")

def transition_to_phase(ctx: InvocationContext, new_phase: str) -> bool:
    """
    Transitions the workflow to a new phase, ensuring validity.
    """
    from .phase_manager import WorkflowPhase, enhanced_phase_manager
    
    state = get_domi_state(ctx)
    current_phase_enum = WorkflowPhase.from_string(state.current_phase)
    new_phase_enum = WorkflowPhase.from_string(new_phase)

    if not new_phase_enum:
        logger.error(f"❌ Invalid target phase '{new_phase}'. Cannot transition.")
        return False

    if enhanced_phase_manager.can_transition(current_phase_enum, new_phase_enum):
        logger.info(f"🔄 Transitioning from {state.current_phase} to {new_phase_enum.value}")
        state.current_phase = new_phase_enum.value
        return True
    else:
        logger.error(f"❌ Invalid transition attempted from {state.current_phase} to {new_phase_enum.value}")
        return False
