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
from ..agents.validators import get_junior_validator_agent, get_senior_validator_agent, ParallelFinalValidationAgent
from .. import config
from ..utils.model_loader import get_llm_model
from ..utils.state_adapter import get_domi_state
from ..utils import directory_manager


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
        domi_state = get_domi_state(ctx)
        original_subtask = domi_state.execution.current_subtask
        original_artifact = domi_state.validation.artifact_to_validate
        original_version = domi_state.validation.validation_version
        original_context = domi_state.validation.validation_context
        
        try:
            domi_state.execution.current_subtask = task
            domi_state.validation.artifact_to_validate = directory_manager.get_coder_output_path(domi_state.task_id, task['task_id'], 0)
            domi_state.validation.validation_version = 0
            domi_state.validation.validation_context = 'code_implementation'
            
            async for event in get_coder_agent().run_async(ctx):
                yield event
        finally:
            domi_state.execution.current_subtask = original_subtask
            domi_state.validation.artifact_to_validate = original_artifact
            domi_state.validation.validation_version = original_version
            domi_state.validation.validation_context = original_context

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
            
            async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
                domi_state = get_domi_state(ctx)
                original_subtask = domi_state.execution.current_subtask
                original_artifact = domi_state.validation.artifact_to_validate
                original_version = domi_state.validation.validation_version
                original_context = domi_state.validation.validation_context
                
                try:
                    domi_state.execution.current_subtask = self._task_data
                    domi_state.validation.artifact_to_validate = directory_manager.get_coder_output_path(domi_state.task_id, self._task_data['task_id'], 0)
                    domi_state.validation.validation_version = 0
                    domi_state.validation.validation_context = 'code_implementation'
                    
                    async for event in get_coder_agent().run_async(ctx):
                        yield event
                finally:
                    domi_state.execution.current_subtask = original_subtask
                    domi_state.validation.artifact_to_validate = original_artifact
                    domi_state.validation.validation_version = original_version
                    domi_state.validation.validation_context = original_context
        
        return TaskSpecificCoderAgent(task)

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """Main entry point for the coder workflow."""
        print("CODER WORKFLOW: Starting parallel coding phase...")
        domi_state = get_domi_state(ctx)
        manifest_path = domi_state.execution.implementation_manifest_artifact
        
        if not manifest_path:
            print("CODER WORKFLOW: Error - No implementation manifest found in session state.")
            from google.genai.types import Content, Part
            yield Event(
                author=self.name,
                content=Content(parts=[Part(text="No implementation manifest found in session state")])
            )
            return
        
        if config.EXECUTION_MODE == "dry_run":
            print("CODER WORKFLOW: [DRY_RUN] Simulating parallel coding tasks...")
            from google.genai.types import Content, Part
            yield Event(
                author=self.name,
                content=Content(parts=[Part(text="[DRY_RUN] Parallel coding tasks completed")])
            )
            return
        
        try:
            import os
            if os.path.exists(manifest_path):
                from ..tools.json_fixer import load_implementation_manifest
                success, manifest_data, message = load_implementation_manifest(manifest_path)
                
                if not success:
                    print(f"CODER WORKFLOW: Failed to parse manifest with fixer: {message}")
                    print("CODER WORKFLOW: Attempting basic JSON parse as fallback...")
                    with open(manifest_path, 'r') as f:
                        manifest_content = f.read()
                    manifest_data = json.loads(manifest_content)
                else:
                    print(f"CODER WORKFLOW: Successfully parsed manifest: {message}")
                
                if isinstance(manifest_data, list):
                    print("CODER WORKFLOW: ⚠️  Warning: Manifest root is a list. Wrapping it in a standard dictionary structure.")
                    manifest_data = {
                        "implementation_plan": {
                            "parallel_tasks": manifest_data
                        }
                    }
                
                if not isinstance(manifest_data, dict):
                    print(f"CODER WORKFLOW: Error - Manifest at {manifest_path} is not a JSON object (dict), but a {type(manifest_data)}.")
                    domi_state.execution.status = 'critical_error'
                    domi_state.execution.error_info.error_type = 'ManifestFormatError'
                    domi_state.execution.error_info.details = f"Manifest root is a {type(manifest_data)}, expected a dict."
                    from google.genai.types import Content, Part
                    yield Event(
                        author=self.name,
                        content=Content(parts=[Part(text=f"Manifest file at {manifest_path} has incorrect format.")])
                    )
                    return

                tasks = manifest_data.get("tasks", [])
                if not tasks:
                    implementation_plan = manifest_data.get("implementation_plan", {})
                    tasks = implementation_plan.get("parallel_tasks", [])
                
                coding_tasks = [t for t in tasks if 'write' in t.get('task_id', '').lower() or 'script' in t.get('description', '').lower()]
                
                if not coding_tasks:
                    print(f"CODER WORKFLOW: No coding tasks found in manifest (found {len(tasks)} total tasks, but none require code generation).")
                    from google.genai.types import Content, Part
                    yield Event(
                        author=self.name,
                        content=Content(parts=[Part(text="No coding tasks found in manifest")])
                    )
                    return
                
                async for event in self._execute_tasks_with_dag_parallelism(ctx, coding_tasks):
                    yield event
                    
                print(f"CODER WORKFLOW: Completed {len(coding_tasks)} coding tasks")
                
            else:
                print(f"CODER WORKFLOW: Manifest file not found: {manifest_path}")
                from google.genai.types import Content, Part
                yield Event(
                    author=self.name,
                    content=Content(parts=[Part(text=f"Manifest file not found: {manifest_path}")])
                )
                
        except json.JSONDecodeError as e:
            print(f"CODER WORKFLOW: Error decoding JSON from manifest: {e}")
            domi_state.execution.status = 'critical_error'
            domi_state.execution.error_info.error_type = 'ManifestFormatError'
            domi_state.execution.error_info.details = f"Could not decode JSON from {manifest_path}."
            from google.genai.types import Content, Part
            yield Event(
                author=self.name,
                content=Content(parts=[Part(text=f"Error reading manifest: {e}")])
            )
        except Exception as e:
            print(f"CODER WORKFLOW: Error reading manifest: {e}")
            domi_state.execution.status = 'critical_error'
            domi_state.execution.error_info.error_type = 'ManifestReadError'
            domi_state.execution.error_info.details = str(e)
            from google.genai.types import Content, Part
            yield Event(
                author=self.name,
                content=Content(parts=[Part(text=f"Error reading manifest: {e}")])
            )

def get_coder_workflow() -> CoderWorkflowAgent:
    """Factory function to create a CoderWorkflowAgent."""
    return CoderWorkflowAgent(name="CoderWorkflow")