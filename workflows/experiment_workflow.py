# /department_of_market_intelligence/workflows/experiment_workflow.py
"""
Workflow for managing experiment execution with validation.
"""
from typing import AsyncGenerator
from google.adk.agents import BaseAgent, SequentialAgent, LoopAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from ..agents.experiment_executor import get_experiment_executor_agent
from ..agents.validators import get_junior_validator_agent, get_senior_validator_agent, MetaValidatorCheckAgent, get_parallel_final_validation_agent
from ..utils.phase_manager import WorkflowPhase
from .. import config
from .coder_workflow import create_validation_loop

class ExperimentWorkflowAgent(BaseAgent):
    """
    Manages the execution and validation of experiments.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._executor_loop = None

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """Main entry point for the experiment workflow."""
        print("EXPERIMENT WORKFLOW: Executor is running the experiments...")
        
        if self._executor_loop is None:
            self._executor_loop = create_validation_loop(
                agent_to_validate=get_experiment_executor_agent(),
                loop_name="ExecutorValidationLoop"
            )

        # Set the context for experiment execution validation
        ctx.session.state['domi_validation_context'] = 'experiment_execution'
        ctx.session.state['domi_artifact_to_validate'] = ctx.session.state.get('domi_execution_log_artifact') or ctx.session.state.get('domi_implementation_manifest_artifact')
        ctx.session.state['domi_validation_version'] = 0
        
        async for event in self._executor_loop.run_async(ctx):
            yield event
        
        if ctx.session.state.get('domi_execution_status') == 'critical_error':
            print("EXPERIMENT WORKFLOW: Critical execution error confirmed by validators. Aborting.")
            return
        
        print("EXPERIMENT WORKFLOW: Experiment execution validated.")


def get_experiment_workflow() -> ExperimentWorkflowAgent:
    """Factory function to create an ExperimentWorkflowAgent."""
    return ExperimentWorkflowAgent(name="ExperimentWorkflow")