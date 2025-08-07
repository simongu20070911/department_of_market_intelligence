# /department_of_market_intelligence/workflows/root_workflow_context_aware.py
"""Context-aware root workflow that uses intelligent validation."""

from typing import AsyncGenerator, Dict, Callable
from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event

from ..agents.chief_researcher import get_chief_researcher_agent
from ..agents.orchestrator import get_orchestrator_agent
from ..agents.coder import get_coder_agent
from ..agents.experiment_executor import get_experiment_executor_agent
from ..agents.validators import get_junior_validator_agent, get_senior_validator_agent, get_meta_validator_check_agent, ParallelFinalValidationAgent
from ..utils.state_adapter import get_domi_state, transition_to_phase
from ..utils.phase_manager import WorkflowPhase, enhanced_phase_manager
from ..utils.logger import get_logger
from .. import config

logger = get_logger(__name__)


class RootWorkflowAgentContextAware(BaseAgent):
    """Context-aware master agent that orchestrates the entire research process."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._agent_factory: Dict[str, Callable[[], BaseAgent]] = {
            "Chief_Researcher": get_chief_researcher_agent,
            "Orchestrator": get_orchestrator_agent,
            "Junior_Validator": get_junior_validator_agent,
            "Senior_Validator": get_senior_validator_agent,
            "Meta_Validator": get_meta_validator_check_agent,
            "Coder_Agent": get_coder_agent,
            "Experiment_Executor": get_experiment_executor_agent,
            "Parallel_Validator": ParallelFinalValidationAgent,
            "System": self.get_system_agent, # Placeholder for system-level actions
        }

    def get_system_agent(self):
        # This can be expanded to a proper agent if system tasks become complex
        return BaseAgent(name="SystemAgent")

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        from ..utils.checkpoint_manager import checkpoint_manager

        domi_state = get_domi_state(ctx)
        checkpoint_manager.task_id = domi_state.task_id

        while True:
            current_phase = WorkflowPhase.from_string(domi_state.current_phase)
            if not current_phase or enhanced_phase_manager.is_terminal_phase(current_phase):
                logger.info(f"🏁 Terminal phase {current_phase.value} reached. Workflow complete.")
                break

            phase_config = enhanced_phase_manager.get_phase_config(current_phase)
            logger.info(f"🚀 Executing Phase: {current_phase.value} (Agent: {phase_config.primary_agent})")

            # Get the agent for the current phase
            agent_factory = self._agent_factory.get(phase_config.primary_agent)
            if not agent_factory:
                logger.error(f"❌ No agent factory found for primary agent: {phase_config.primary_agent}")
                transition_to_phase(ctx, WorkflowPhase.ERROR.value)
                continue
            
            agent = agent_factory()

            # Execute the agent
            async for event in agent.run_async(ctx):
                yield event

            # Determine the outcome of the phase
            domi_state = get_domi_state(ctx) # Refresh state
            validation_status = domi_state.validation.validation_status
            error_occurred = domi_state.metadata.get("error_occurred", False)

            next_phase = None
            # Determine the next phase based on the outcome
            next_phase = enhanced_phase_manager.determine_next_phase(
                current_phase,
                validation_status,
                error_occurred
            )


            if next_phase and enhanced_phase_manager.can_transition(current_phase, next_phase):
                transition_to_phase(ctx, next_phase.value)
                checkpoint_manager.save_state_snapshot(get_domi_state(ctx), next_phase.value)
            else:
                logger.error(f"❌ Invalid or no next phase defined from {current_phase.value}. Halting workflow.")
                transition_to_phase(ctx, WorkflowPhase.ERROR.value)
                break
        
        logger.info("✅ Workflow finished.")


def get_context_aware_root_workflow():
    """Factory function to create context-aware root workflow."""
    return RootWorkflowAgentContextAware(name="ContextAwareRootWorkflow")