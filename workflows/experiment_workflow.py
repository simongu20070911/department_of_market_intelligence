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
from .. import config

def _create_validation_loop(agent_to_validate: BaseAgent, loop_name: str, max_loops: int = 5) -> SequentialAgent:
    """Helper factory to create a standard refinement/validation loop for an agent with final parallel validation."""
    main_loop = LoopAgent(
        name=loop_name,
        max_iterations=max_loops,
        sub_agents=[
            SequentialAgent(
                name=f"{agent_to_validate.name}_And_Validate_Seq",
                sub_agents=[
                    agent_to_validate,
                    get_junior_validator_agent(),
                    get_senior_validator_agent(),
                    MetaValidatorCheckAgent(name=f"{agent_to_validate.name}_MetaCheck")
                ]
            )
        ]
    )
    
    return SequentialAgent(
        name=f"{loop_name}_WithParallelValidation",
        sub_agents=[
            main_loop,
            get_parallel_final_validation_agent()
        ]
    )

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
            self._executor_loop = _create_validation_loop(
                agent_to_validate=get_experiment_executor_agent(),
                loop_name="ExecutorValidationLoop"
            )

        ctx.session.state['artifact_to_validate'] = ctx.session.state['implementation_manifest_artifact']
        ctx.session.state['validation_version'] = 0
        async for event in self._executor_loop.run_async(ctx):
            yield event
        
        if ctx.session.state.get('execution_status') == 'critical_error':
            print("EXPERIMENT WORKFLOW: Critical execution error confirmed by validators. Aborting.")
            return
        
        print("EXPERIMENT WORKFLOW: Experiment execution validated.")


def get_experiment_workflow() -> ExperimentWorkflowAgent:
    """Factory function to create an ExperimentWorkflowAgent."""
    return ExperimentWorkflowAgent(name="ExperimentWorkflow")