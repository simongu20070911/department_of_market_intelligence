# /department_of_market_intelligence/workflows/coder_workflow.py
"""
Workflow for managing parallel coding tasks with validation.
"""
import json
from typing import AsyncGenerator
from google.adk.agents import BaseAgent, SequentialAgent, ParallelAgent, LoopAgent, LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from ..agents.coder import get_coder_agent
from ..agents.validators import get_junior_validator_agent, get_senior_validator_agent, MetaValidatorCheckAgent, get_parallel_final_validation_agent
from .. import config
from ..utils.model_loader import get_llm_model




def create_validation_loop(agent_to_validate: BaseAgent, loop_name: str, max_loops: int = 5) -> SequentialAgent:
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

class CoderWorkflowAgent(BaseAgent):
    """
    Manages the execution of parallel coding tasks based on a manifest.
    Each task is executed and validated independently.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._coder_validation_loop_template = None

    async def _execute_tasks_with_dag_parallelism(self, ctx: InvocationContext, tasks: list) -> AsyncGenerator[Event, None]:
        """Execute coding tasks in parallel following DAG dependency constraints."""
        completed_tasks = set()
        tasks_by_id = {task['task_id']: task for task in tasks}
        
        while len(completed_tasks) < len(tasks):
            ready_tasks = []
            for task in tasks:
                task_id = task['task_id']
                if task_id not in completed_tasks:
                    dependencies = set(task.get('dependencies', []))
                    if dependencies.issubset(completed_tasks):
                        ready_tasks.append(task)
            
            if not ready_tasks:
                remaining = [t['task_id'] for t in tasks if t['task_id'] not in completed_tasks]
                print(f"CODER WORKFLOW: Warning - No ready tasks found. Remaining: {remaining}")
                break
            
            print(f"CODER WORKFLOW: Executing {len(ready_tasks)} tasks in parallel: {[t['task_id'] for t in ready_tasks]}")
            
            if len(ready_tasks) == 1:
                task = ready_tasks[0]
                print(f"  - Starting coding task: {task['task_id']}")
                async for event in self._execute_single_coding_task(ctx, task):
                    yield event
                completed_tasks.add(task['task_id'])
                print(f"  - Completed coding task: {task['task_id']}")
            else:
                async for event in self._execute_parallel_coding_tasks(ctx, ready_tasks):
                    yield event
                for task in ready_tasks:
                    completed_tasks.add(task['task_id'])
                    print(f"  - Completed coding task: {task['task_id']}")

    async def _execute_single_coding_task(self, ctx: InvocationContext, task: dict) -> AsyncGenerator[Event, None]:
        """Execute a single coding task with validation."""
        original_subtask = ctx.session.state.get('coder_subtask')
        original_artifact = ctx.session.state.get('artifact_to_validate')
        original_version = ctx.session.state.get('validation_version')
        original_context = ctx.session.state.get('validation_context')
        
        try:
            ctx.session.state['coder_subtask'] = task
            ctx.session.state['artifact_to_validate'] = f"coder_output_{task['task_id']}"
            ctx.session.state['validation_version'] = 0
            # Set the specific context for code validation
            ctx.session.state['validation_context'] = 'code_implementation'
            
            if self._coder_validation_loop_template is None:
                 self._coder_validation_loop_template = create_validation_loop(
                    agent_to_validate=get_coder_agent(),
                    loop_name="CoderValidationLoop",
                    max_loops=config.MAX_CODE_REFINEMENT_LOOPS
                )
            
            async for event in self._coder_validation_loop_template.run_async(ctx):
                yield event
        finally:
            # Restore original state
            ctx.session.state['coder_subtask'] = original_subtask
            ctx.session.state['artifact_to_validate'] = original_artifact
            ctx.session.state['validation_version'] = original_version
            ctx.session.state['validation_context'] = original_context

    async def _execute_parallel_coding_tasks(self, ctx: InvocationContext, tasks: list) -> AsyncGenerator[Event, None]:
        """Execute multiple coding tasks in parallel using ParallelAgent."""
        parallel_coders = [self._create_task_specific_coder_agent(task) for task in tasks]
        
        parallel_execution = ParallelAgent(
            name=f"ParallelCoders_{len(tasks)}Tasks",
            sub_agents=parallel_coders
        )
        
        print(f"  - Starting {len(tasks)} parallel coding tasks: {[t['task_id'] for t in tasks]}")
        async for event in parallel_execution.run_async(ctx):
            yield event

    def _create_task_specific_coder_agent(self, task: dict) -> BaseAgent:
        """Create a task-specific coder agent that handles its own state management."""
        class TaskSpecificCoderAgent(BaseAgent):
            def __init__(self, task_data: dict):
                super().__init__(name=f"Coder_{task_data['task_id']}")
                self._task_data = task_data
                self._validation_loop = None
            
            async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
                if self._validation_loop is None:
                    self._validation_loop = create_validation_loop(
                        agent_to_validate=get_coder_agent(),
                        loop_name=f"CoderValidationLoop_{self._task_data['task_id']}",
                        max_loops=config.MAX_CODE_REFINEMENT_LOOPS
                    )
                
                original_subtask = ctx.session.state.get('coder_subtask')
                original_artifact = ctx.session.state.get('artifact_to_validate')
                original_version = ctx.session.state.get('validation_version')
                original_context = ctx.session.state.get('validation_context')
                
                try:
                    ctx.session.state['coder_subtask'] = self._task_data
                    ctx.session.state['artifact_to_validate'] = f"coder_output_{self._task_data['task_id']}"
                    ctx.session.state['validation_version'] = 0
                    # Set the specific context for code validation
                    ctx.session.state['validation_context'] = 'code_implementation'
                    
                    async for event in self._validation_loop.run_async(ctx):
                        yield event
                finally:
                    # Restore original state
                    ctx.session.state['coder_subtask'] = original_subtask
                    ctx.session.state['artifact_to_validate'] = original_artifact
                    ctx.session.state['validation_version'] = original_version
                    ctx.session.state['validation_context'] = original_context
        
        return TaskSpecificCoderAgent(task)

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """Main entry point for the coder workflow."""
        print("CODER WORKFLOW: Starting parallel coding phase...")
        manifest_path = ctx.session.state.get('implementation_manifest_artifact')
        
        if not manifest_path:
            print("CODER WORKFLOW: Error - No implementation manifest found in session state.")
            # Need to yield something to make this an async generator
            from google.adk.events import Event
            from google.genai.types import Content, Part
            yield Event(
                author=self.name,
                content=Content(parts=[Part(text="No implementation manifest found in session state")])
            )
            return
        
        # In dry run mode, just simulate the coding tasks
        if config.EXECUTION_MODE == "dry_run":
            print("CODER WORKFLOW: [DRY_RUN] Simulating parallel coding tasks...")
            from google.adk.events import Event
            from google.genai.types import Content, Part
            yield Event(
                author=self.name,
                content=Content(parts=[Part(text="[DRY_RUN] Parallel coding tasks completed")])
            )
            
            # Set some mock coding tasks for state tracking - need to use metadata since direct assignment won't work with Pydantic
            from ..utils.state_adapter import StateProxy
            state_proxy = StateProxy(getattr(ctx.session, '_typed_state', None))
            
            # Store in metadata instead of direct assignment to avoid Pydantic validation
            state_proxy['metadata']['mock_coding_tasks'] = [
                {'task_id': 'mock_task_1', 'description': 'Mock coding task 1', 'status': 'completed'},
                {'task_id': 'mock_task_2', 'description': 'Mock coding task 2', 'status': 'completed'}
            ]
            return
        
        # Read the manifest file to get tasks
        try:
            import os
            if os.path.exists(manifest_path):
                with open(manifest_path, 'r') as f:
                    manifest_content = f.read()
                
                # Parse tasks from manifest, expecting a specific structure
                manifest_data = json.loads(manifest_content)
                
                # FIX: Handle case where manifest is a list instead of a dict
                if isinstance(manifest_data, list):
                    print("CODER WORKFLOW: ⚠️  Warning: Manifest root is a list. Wrapping it in a standard dictionary structure.")
                    manifest_data = {
                        "implementation_plan": {
                            "parallel_tasks": manifest_data
                        }
                    }
                
                if not isinstance(manifest_data, dict):
                    print(f"CODER WORKFLOW: Error - Manifest at {manifest_path} is not a JSON object (dict), but a {type(manifest_data)}.")
                    # SET FAILURE STATE to halt the parent workflow
                    ctx.session.state['execution_status'] = 'critical_error'
                    ctx.session.state['error_type'] = 'ManifestFormatError'
                    ctx.session.state['error_details'] = f"Manifest root is a {type(manifest_data)}, expected a dict."
                    from google.adk.events import Event
                    from google.genai.types import Content, Part
                    yield Event(
                        author=self.name,
                        content=Content(parts=[Part(text=f"Manifest file at {manifest_path} has incorrect format.")])
                    )
                    return

                # Try multiple possible structures for backward compatibility
                tasks = manifest_data.get("tasks", [])  # Direct tasks array (current format)
                if not tasks:
                    # Fallback to nested structure (legacy format)
                    implementation_plan = manifest_data.get("implementation_plan", {})
                    tasks = implementation_plan.get("parallel_tasks", [])
                
                # Filter for actual coding tasks (ones that need code generation)
                coding_tasks = [t for t in tasks if 'write' in t.get('task_id', '').lower() or 'script' in t.get('description', '').lower()]
                
                if not coding_tasks:
                    print(f"CODER WORKFLOW: No coding tasks found in manifest (found {len(tasks)} total tasks, but none require code generation).")
                    from google.adk.events import Event
                    from google.genai.types import Content, Part
                    yield Event(
                        author=self.name,
                        content=Content(parts=[Part(text="No coding tasks found in manifest")])
                    )
                    return
                
                # Execute tasks with DAG parallelism
                async for event in self._execute_tasks_with_dag_parallelism(ctx, coding_tasks):
                    yield event
                    
                print(f"CODER WORKFLOW: Completed {len(coding_tasks)} coding tasks")
                
            else:
                print(f"CODER WORKFLOW: Manifest file not found: {manifest_path}")
                from google.adk.events import Event
                from google.genai.types import Content, Part
                yield Event(
                    author=self.name,
                    content=Content(parts=[Part(text=f"Manifest file not found: {manifest_path}")])
                )
                
        except json.JSONDecodeError as e:
            print(f"CODER WORKFLOW: Error decoding JSON from manifest: {e}")
            ctx.session.state['execution_status'] = 'critical_error'
            ctx.session.state['error_type'] = 'ManifestFormatError'
            ctx.session.state['error_details'] = f"Could not decode JSON from {manifest_path}."
            from google.adk.events import Event
            from google.genai.types import Content, Part
            yield Event(
                author=self.name,
                content=Content(parts=[Part(text=f"Error reading manifest: {e}")])
            )
        except Exception as e:
            print(f"CODER WORKFLOW: Error reading manifest: {e}")
            ctx.session.state['execution_status'] = 'critical_error'
            ctx.session.state['error_type'] = 'ManifestReadError'
            ctx.session.state['error_details'] = str(e)
            from google.adk.events import Event
            from google.genai.types import Content, Part
            yield Event(
                author=self.name,
                content=Content(parts=[Part(text=f"Error reading manifest: {e}")])
            )



def get_coder_workflow() -> CoderWorkflowAgent:
    """Factory function to create a CoderWorkflowAgent."""
    return CoderWorkflowAgent(name="CoderWorkflow")