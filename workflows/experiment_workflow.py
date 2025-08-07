# /department_of_market_intelligence/workflows/experiment_workflow.py
"""
Workflow for managing experiment execution with validation.
"""
from typing import AsyncGenerator
from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from ..agents.experiment_executor import get_experiment_executor_agent
from .validation_utils import create_validation_loop
from ..utils.state_adapter import get_domi_state

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

        async for event in self._executor_loop.run_async(ctx):
            yield event
        
        domi_state = get_domi_state(ctx)
        if domi_state.execution.status == 'critical_error':
            print("EXPERIMENT WORKFLOW: Critical execution error confirmed by validators. Aborting.")
            return
        
        print("EXPERIMENT WORKFLOW: Experiment execution validated.")


def get_experiment_workflow() -> ExperimentWorkflowAgent:
    """Factory function to create an ExperimentWorkflowAgent."""
    return ExperimentWorkflowAgent(name="ExperimentWorkflow")