# /department_of_market_intelligence/workflows/implementation_workflow.py
import json
from typing import AsyncGenerator
from google.adk.agents import BaseAgent, SequentialAgent, ParallelAgent, LoopAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from ..agents.orchestrator import get_orchestrator_agent
from ..agents.coder import get_coder_agent
from ..agents.executor import get_experiment_executor_agent
from ..agents.validators import get_junior_validator_agent, get_senior_validator_agent, MetaValidatorCheckAgent
from .. import config
from ..tools.desktop_commander import desktop_commander_toolset # Need for file reading

class ImplementationWorkflowAgent(BaseAgent):
    """A custom agent to manage the entire implementation and execution phase."""

    def __init__(self, **kwargs):
        # Initialize parent first
        super().__init__(**kwargs)
        
        # Store agent references as private attributes after initialization
        self._orchestrator_planning_loop = None
        self._executor_loop = None
        self._results_extraction_loop = None
        self._coder_validation_loop_template = None

    def _create_validation_loop(self, agent_to_validate: BaseAgent, loop_name: str, max_loops: int = 5) -> LoopAgent:
        """Helper factory to create a standard refinement/validation loop for an agent."""
        return LoopAgent(
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

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        # Create agents lazily on first use
        if self._orchestrator_planning_loop is None:
            self._orchestrator_planning_loop = self._create_validation_loop(
                agent_to_validate=get_orchestrator_agent(),
                loop_name="OrchestratorPlanningLoop"
            )
            self._executor_loop = self._create_validation_loop(
                agent_to_validate=get_experiment_executor_agent(),
                loop_name="ExecutorValidationLoop"
            )
            self._results_extraction_loop = self._create_validation_loop(
                agent_to_validate=get_orchestrator_agent(),
                loop_name="ResultsExtractionLoop"
            )
            self._coder_validation_loop_template = self._create_validation_loop(
                agent_to_validate=get_coder_agent(),
                loop_name="CoderValidationLoop",
                max_loops=config.MAX_CODE_REFINEMENT_LOOPS
            )
        
        # 1. Orchestrator generates the implementation manifest
        print("IMPLEMENTATION WORKFLOW: Orchestrator is generating the implementation plan...")
        ctx.session.state['artifact_to_validate'] = ctx.session.state['plan_artifact_name']
        ctx.session.state['validation_version'] = 0
        async for event in self._orchestrator_planning_loop.run_async(ctx):
            yield event
        print("IMPLEMENTATION WORKFLOW: Implementation plan approved.")

        # 2. Read the manifest to set up parallel coding
        manifest_path = ctx.session.state['implementation_manifest_artifact']
        # Use the tool directly within the custom agent to read the file
        # This requires the tool to be available, but we don't add it to this agent's
        # `tools` list for the LLM. We call it programmatically.
        manifest_content_response = await desktop_commander_toolset.get_tools()[0].run_async(
            args={'path': manifest_path}, tool_context=None
        )
        tasks = json.loads(manifest_content_response['content'])
        
        # 3. Dynamically create and run parallel coding loops
        print(f"IMPLEMENTATION WORKFLOW: Starting parallel coding phase for {len(tasks)} tasks...")
        
        # Simple sequential execution based on dependencies for this example.
        # A true parallel execution would require a dependency graph solver.
        completed_tasks = set()
        for _ in range(len(tasks)): # Failsafe loop
            tasks_to_run_this_iteration = []
            for task in tasks:
                if task['task_id'] not in completed_tasks and set(task.get('dependencies', [])).issubset(completed_tasks):
                    tasks_to_run_this_iteration.append(task)
            
            if not tasks_to_run_this_iteration:
                # Either all done or a dependency cycle/error exists
                break

            parallel_coders = []
            for task in tasks_to_run_this_iteration:
                # Create a "contextualized" agent for this specific task
                # by setting its initial state. ADK doesn't have a direct way to pass
                # different states to parallel agents, so we manage it here.
                # This is an advanced pattern.
                # In a real app, you might create unique agent instances per task.
                # For now, we'll rely on the agent reading its task from a unique state key.
                # This part is complex and highlights a frontier in agent orchestration.
                # A simpler model is to run them sequentially if true parallelism is hard.
                
                # Let's simplify to sequential execution for clarity and robustness.
                print(f"  - Starting coding task: {task['task_id']}")
                ctx.session.state['coder_subtask'] = task
                ctx.session.state['artifact_to_validate'] = "coder_output" # Coder agent should create this
                ctx.session.state['validation_version'] = 0
                async for event in self._coder_validation_loop_template.run_async(ctx):
                    yield event
                completed_tasks.add(task['task_id'])
                print(f"  - Completed coding task: {task['task_id']}")

        print("IMPLEMENTATION WORKFLOW: All coding tasks complete.")

        # 4. Execute the experiments
        print("IMPLEMENTATION WORKFLOW: Executor is running the experiments...")
        ctx.session.state['artifact_to_validate'] = ctx.session.state['implementation_manifest_artifact']
        ctx.session.state['validation_version'] = 0
        async for event in self._executor_loop.run_async(ctx):
            yield event
        print("IMPLEMENTATION WORKFLOW: Experiment execution validated.")

        # 5. Orchestrator generates the results extraction script
        print("IMPLEMENTATION WORKFLOW: Orchestrator is planning results extraction...")
        ctx.session.state['current_task'] = 'generate_results_extraction_plan'
        ctx.session.state['artifact_to_validate'] = ctx.session.state['implementation_manifest_artifact']
        ctx.session.state['validation_version'] = 0
        async for event in self._results_extraction_loop.run_async(ctx):
            yield event
        print("IMPLEMENTATION WORKFLOW: Results extraction plan approved.")

        # 6. Execute the results extraction script
        print("IMPLEMENTATION WORKFLOW: Executing results extraction script...")
        extraction_script_path = ctx.session.state['results_extraction_script_artifact']
        # Use the executor agent one last time to run the final script
        ctx.session.state['execution_status'] = 'pending' # Reset status
        # We can reuse the executor agent directly here
        async for event in get_experiment_executor_agent().run_async(ctx):
             # This is a simplified call; the executor's prompt would need to handle this specific task
             yield event
        
        # The final results are now in an artifact, ready for the Chief Researcher
        # The root workflow will handle the final reporting step.