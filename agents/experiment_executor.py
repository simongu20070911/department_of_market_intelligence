# /department_of_market_intelligence/agents/executor.py
import asyncio
import os
import json
from typing import Dict, Any, List, AsyncGenerator
from google.adk.agents import LlmAgent
from google.adk.agents.llm_agent import ReadonlyContext
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from google.genai.types import Content, Part

from .. import config
from ..utils.callbacks import ensure_end_of_output
from ..utils.model_loader import get_llm_model
from ..utils.state_adapter import get_domi_state
from ..utils.checkpoint_manager import CheckpointManager, TrackedOperation
from ..prompts.definitions.experiment_executor import EXPERIMENT_EXECUTOR_INSTRUCTION


class MicroCheckpointExperimentExecutor(LlmAgent):
    """Experiment Executor with micro-checkpoint support for fine-grained recovery."""
    
    def __init__(self, model, tools, instruction_provider, **kwargs):
        kwargs.setdefault('after_model_callback', ensure_end_of_output)
        super().__init__(
            model=model,
            name="Experiment_Executor",
            instruction=instruction_provider,
            tools=tools,
            **kwargs
        )
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """Enhanced execution with fine-grained checkpointing."""
        domi_state = get_domi_state(ctx)
        task_id = domi_state.task_id
        checkpoint_manager = CheckpointManager(task_id)

        if domi_state.current_task_description == 'execute_results_extraction':
            print("[Experiment_Executor]: Bypassing manifest parsing for single-script execution task.")
            async for event in super()._run_async_impl(ctx):
                yield event
            return
        
        if not config.ENABLE_MICRO_CHECKPOINTS:
            print("[Experiment_Executor]: Micro-checkpoints disabled, running standard execution.")
            async for event in super()._run_async_impl(ctx):
                yield event
            return
        
        execution_executed_key = f"executor_planning_executed_v{domi_state.validation.validation_version}_for_{task_id}"

        if domi_state.metadata.get(execution_executed_key):
            print(f"[Experiment_Executor]: Micro-checkpoint execution planning already completed. Running LLM agent directly.")
            async for event in super()._run_async_impl(ctx):
                yield event
            return
        
        recoverable_ops = checkpoint_manager.list_recoverable_operations(agent_name="Experiment_Executor")
        if recoverable_ops and config.MICRO_CHECKPOINT_AUTO_RESUME:
            print(f"[Experiment_Executor]: Found {len(recoverable_ops)} recoverable experiment operations. Resuming...")
            for op_info in recoverable_ops:
                operation = checkpoint_manager.resume_operation(op_info['operation_id'])
                if operation:
                    await self._execute_tracked_operation(ctx, operation)
            return
        
        implementation_plan_path = domi_state.execution.implementation_manifest_artifact
        if not implementation_plan_path:
            print("[Experiment_Executor]: ⚠️  No implementation plan found - running standard execution.")
            async for event in super()._run_async_impl(ctx):
                yield event
            return
        
        experiments = await self._parse_implementation_plan(implementation_plan_path)
        if not experiments:
            print("[Experiment_Executor]: No executable experiments found in manifest.")
            # Handle no experiments case...
            return
        
        operation_id = f"execute_experiments_{task_id}_{int(asyncio.get_event_loop().time())}"
        operation = checkpoint_manager.create_operation(operation_id, "Experiment_Executor", experiments)
        
        await self._execute_tracked_operation(ctx, operation)
        
        domi_state.metadata[execution_executed_key] = True
        print("[Experiment_Executor]: Running LLM agent to analyze execution results...")
        async for event in super()._run_async_impl(ctx):
            yield event

    async def _execute_tracked_operation(self, ctx: InvocationContext, operation: TrackedOperation):
        """Executes all steps in a tracked operation."""
        print(f"[Experiment_Executor]: Executing operation '{operation.operation_id}' with {len(operation.get_remaining_steps())} steps.")
        
        with operation as (tracker, steps):
            tasks = [self._run_step(step, ctx, tracker) for step in steps]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            successful_results = [res for res in results if not isinstance(res, Exception)]
            await self._create_execution_summary(ctx, successful_results, operation.operation_id)

    async def _run_step(self, step, ctx, tracker):
        """Executes a single step within a tracked context."""
        with tracker.step_context(step):
            try:
                result = await self._execute_single_experiment(ctx, step.input_state)
                print(f"[Experiment_Executor]: ✅ Completed experiment: {step.step_name}")
                return result
            except Exception as e:
                print(f"[Experiment_Executor]: ❌ Experiment step failed: {step.step_name} - {e}")
                raise
    
    async def _parse_implementation_plan(self, plan_path: str) -> List[Dict[str, Any]]:
        """Parse implementation plan from JSON manifest to extract experiment configurations."""
        try:
            # Check if plan_path is actually a path or raw content
            if not os.path.exists(plan_path):
                print(f"[Experiment_Executor]: ⚠️  Implementation plan path does not exist. Assuming content is raw JSON.")
                manifest_data = json.loads(plan_path)
            else:
                # Use the smart JSON fixer to handle LLM-generated JSON issues
                from ..tools.json_fixer import load_implementation_manifest
                success, manifest_data, message = load_implementation_manifest(plan_path)
                
                if not success:
                    print(f"[Experiment_Executor]: ❌ Failed to parse manifest with fixer: {message}")
                    print("[Experiment_Executor]: ⚠️  Attempting basic JSON parse as fallback...")
                    with open(plan_path, 'r') as f:
                        manifest_data = json.load(f)
                else:
                    print(f"[Experiment_Executor]: ✅ Successfully parsed manifest: {message}")

            # FIX: Handle case where manifest is a list instead of a dict
            if isinstance(manifest_data, list):
                print("[Experiment_Executor]: ⚠️  Warning: Manifest root is a list. Wrapping it in a standard dictionary structure.")
                manifest_data = {
                    "implementation_plan": {
                        "parallel_tasks": manifest_data
                    }
                }

            if not isinstance(manifest_data, dict):
                print(f"[Experiment_Executor]: ❌ Error parsing implementation plan: Manifest root is not a JSON object, but {type(manifest_data)}")
                return []

            # Try multiple possible structures for backward compatibility
            tasks = manifest_data.get("tasks", [])  # Direct tasks array (current format)
            if not tasks:
                # Fallback to nested structure (legacy format)
                implementation_plan = manifest_data.get("implementation_plan", {})
                tasks = implementation_plan.get("parallel_tasks", [])

            if not isinstance(tasks, list):
                print(f"[Experiment_Executor]: ❌ Error parsing implementation plan: 'tasks' field is not a list.")
                return []

            # Convert manifest tasks into experiment configurations
            # Include all tasks that involve data processing or computation
            # Expanded keyword list to catch more experiment types
            execution_keywords = [
                'run', 'aggregate', 'analyze', 'compile', 'simulation', 
                'analysis', 'processing', 'compute', 'calculate', 'generate',
                'execute', 'evaluation', 'test', 'experiment', 'visualization',
                'visualizations', 'chart', 'plot', 'graph', 'data'
            ]
            
            execution_tasks = [t for t in tasks if any(keyword in t.get('task_id', '').lower() 
                for keyword in execution_keywords)]
            
            experiments = []
            for i, task in enumerate(execution_tasks):
                task_id = task.get("task_id", f"task_{i+1}")
                
                # Determine the type of task and appropriate script/arguments
                # Use task_id to generate script name
                script_path = f"workspace/scripts/{task_id}.py"
                
                # Build arguments based on task structure
                arguments = ""
                
                # Special handling for known task patterns
                if 'simulation' in task_id.lower():
                    # Simulation tasks may need special flags
                    if 'data_simulation' == task_id:
                        # Main data simulation task
                        arguments = "--trials 10 --samples 10000"
                    else:
                        # Other simulation tasks
                        sim_id = task_id.split('_')[-1] if '_' in task_id else str(i+1)
                        arguments = f"--simulation-id {sim_id}"
                elif 'aggregate' in task_id.lower():
                    # Aggregation task - run with --aggregate flag
                    arguments = "--aggregate"
                elif 'statistical_analysis' == task_id:
                    # Statistical analysis task
                    arguments = "--input simulation_results.csv --output statistical_results.json"
                elif 'visualizations' == task_id:
                    # Visualization generation task
                    arguments = "--input simulation_results.csv --generate-charts"
                elif 'report' in task_id.lower() or 'compile' in task_id.lower():
                    # Report compilation - might be a separate script or manual task
                    continue  # Skip for now, handle in results phase
                
                experiments.append({
                    "name": task.get("description", f"Task: {task_id}"),
                    "type": "python_script",
                    "script_path": script_path,
                    "arguments": arguments,
                    "task_id": task_id,
                    "dependencies": task.get("dependencies", []),
                    "output_artifacts": task.get("output_artifacts", [])
                })
            
            return experiments
            
        except json.JSONDecodeError as e:
            print(f"[Experiment_Executor]: ❌ Error decoding JSON from implementation plan: {e}")
            return []
        except Exception as e:
            print(f"[Experiment_Executor]: ❌ Error parsing implementation plan: {e}")
            return []
    
    def _find_tool(self, tool_name: str):
        """Finds a tool by name from the agent's tool list."""
        for tool in self.tools:
            # Check if it's a regular tool with a name attribute
            if hasattr(tool, 'name') and tool.name == tool_name:
                return tool
            if hasattr(tool, 'get_tools'):
                for mcp_tool in tool.get_tools():
                    if mcp_tool.name.endswith(f"__{tool_name}"):
                        return mcp_tool
        raise ValueError(f"Tool '{tool_name}' not found in agent's toolset.")

    async def _execute_single_experiment(self, ctx: InvocationContext, experiment_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single experiment by running its script."""
        
        experiment_name = experiment_config.get("name", "Unknown_Experiment")
        script_command = experiment_config.get("code")
        
        if not script_command:
            raise ValueError(f"No 'code' command found in experiment config for '{experiment_name}'")

        print(f"[Experiment_Executor]:    - Executing: {experiment_name} -> `{script_command}`")

        try:
            exec_tool = self._find_tool("run_script_in_terminal")
        except ValueError:
            exec_tool = self._find_tool("execute_shell_command")

        # --- FIX: Correctly iterate over the tool's async generator to get the result ---
        tool_result = None
        tool_event_generator = exec_tool.run_async(
            args={'command': script_command},
            tool_context=None
        )
        
        async for event in tool_event_generator:
            # The tool result is in the function_response of the final event
            if event.is_final_response() and event.get_function_responses():
                tool_result = event.get_function_responses()[0].response
        # --- END FIX ---
        
        print(f"[Experiment_Executor]:    - Execution result for '{experiment_name}':\n{tool_result}")

        status = "completed"
        if isinstance(tool_result, dict) and tool_result.get('status') == 'error':
            status = "failed"
            raise RuntimeError(f"Execution of '{experiment_name}' failed: {tool_result.get('error_message', 'Unknown error')}")

        return {
            "experiment_name": experiment_name,
            "status": status,
            "method": "micro_checkpoint_execution",
            "output": tool_result,
            "config": experiment_config
        }
    
    async def _create_execution_summary(self, ctx: InvocationContext, results: List[Dict[str, Any]], operation_id: str):
        """Create a summary of all experiment executions."""
        domi_state = get_domi_state(ctx)
        task_id = domi_state.task_id
        outputs_dir = config.get_outputs_dir(task_id)
        
        summary = {
            "domi_task_id": task_id,
            "operation_id": operation_id,
            "total_experiments": len(results),
            "successful_experiments": len([r for r in results if r.get("status") == "completed"]),
            "failed_experiments": len([r for r in results if r.get("status") != "completed"]),
            "execution_details": results,
            "micro_checkpoints_used": True
        }
        
        summary_path = os.path.join(outputs_dir, "execution", f"execution_summary_{operation_id}.json")
        os.makedirs(os.path.dirname(summary_path), exist_ok=True)
        
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        domi_state.execution.execution_log_artifact = summary_path
        domi_state.metadata['micro_checkpoints_enabled'] = True
        
        print(f"[Experiment_Executor]: 💾 Micro-checkpoint summary created at: {summary_path}")


def get_experiment_executor_agent():
    """Create Experiment Executor agent with micro-checkpoint support."""
    agent_name = "Experiment_Executor"
    
    # Get tools from the registry
    from ..tools.toolset_registry import toolset_registry
    desktop_commander_toolset = toolset_registry.get_desktop_commander_toolset()
    
    # Wrap in list if it's a real MCP toolset, mock tools are already a list
    tools = [desktop_commander_toolset] if toolset_registry.is_using_real_mcp() else desktop_commander_toolset
        
    def instruction_provider(ctx: "ReadonlyContext") -> str:
        from ..prompts.builder import inject_template_variables_with_context_preloading
        return inject_template_variables_with_context_preloading(EXPERIMENT_EXECUTOR_INSTRUCTION, ctx, agent_name)
    
    agent = MicroCheckpointExperimentExecutor(
        model=get_llm_model(config.EXECUTOR_MODEL),
        instruction_provider=instruction_provider,
        tools=tools,
        output_key="domi_execution_log_artifact"
    )
    
    return agent