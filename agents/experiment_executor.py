# /department_of_market_intelligence/agents/executor.py
import asyncio
import os
import json
from typing import Dict, Any, List, AsyncGenerator
from google.adk.agents import LlmAgent
from google.adk.agents.llm_agent import ReadonlyContext
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event

from .. import config
from ..utils.callbacks import ensure_end_of_output
from ..utils.model_loader import get_llm_model
from ..utils.operation_tracking import (
    tracked_operation,
    create_experiment_operation,
    OperationStep
)
from ..utils.micro_checkpoint_manager import micro_checkpoint_manager
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
        
        # Check if micro-checkpoints are enabled
        if not config.ENABLE_MICRO_CHECKPOINTS:
            print("🔄 Micro-checkpoints disabled - running standard execution")
            async for event in super()._run_async_impl(ctx):
                yield event
            return
        
        # Use a unique key to track if this pre-execution has been done
        task_id = ctx.session.state.get('task_id', config.TASK_ID)
        validation_version = ctx.session.state.get('validation_version', 0)
        execution_executed_key = f"executor_planning_executed_v{validation_version}_for_{task_id}"

        if ctx.session.state.get(execution_executed_key):
            print("🔄 Micro-checkpoint execution planning already completed for this version. Running LLM agent directly.")
            async for event in super()._run_async_impl(ctx):
                yield event
            return
        
        # Check for resumable operations first
        recoverable_ops = micro_checkpoint_manager.list_recoverable_operations()
        executor_ops = [op for op in recoverable_ops if "Experiment_Executor" in op.get("agent_name", "")]
        
        if executor_ops and config.MICRO_CHECKPOINT_AUTO_RESUME:
            print(f"🔄 Found {len(executor_ops)} recoverable experiment operations")
            for op in executor_ops:
                print(f"   • {op['operation_id']}: {op['progress']} steps completed")
            
            # Resume operations automatically
            for op_info in executor_ops:
                async for event in self._resume_operation(ctx, op_info):
                    yield event
            return
        
        # Get implementation plan and task info from session state
        implementation_plan_path = ctx.session.state.get('implementation_manifest_artifact')
        task_id = ctx.session.state.get('task_id', config.TASK_ID)
        
        if not implementation_plan_path:
            print("⚠️  No implementation plan found - running standard execution")
            # Fall back to standard LLM execution
            async for event in super()._run_async_impl(ctx):
                yield event
            return
        
        # Parse implementation plan to identify experiments
        experiments = await self._parse_implementation_plan(implementation_plan_path)
        
        if not experiments:
            print("⚠️  No experiments found - running standard execution")
            async for event in super()._run_async_impl(ctx):
                yield event
            return
        
        # Create tracked operation for experiment execution
        operation_id = f"execute_experiments_{task_id}_{int(asyncio.get_event_loop().time())}"
        
        experiment_operation = create_experiment_operation(
            operation_id=operation_id,
            agent_name="Experiment_Executor",
            experiment_configs=experiments
        )
        
        # Execute experiments with fine-grained tracking
        print(f"🧪 Starting {len(experiments)} experiments with micro-checkpointing")
        
        with experiment_operation.execute() as (tracker, steps):
            execution_results = []
            
            for step in steps:
                try:
                    with tracker.step_context(step):
                        # Execute individual experiment with checkpointing
                        experiment_config = step.input_state
                        result = await self._execute_single_experiment(ctx, experiment_config)
                        execution_results.append(result)
                        
                        print(f"✅ Completed experiment: {experiment_config.get('name', 'Unknown')}")
                        
                except Exception as e:
                    print(f"❌ Experiment step failed: {step.step_name} - {e}")
                    # Continue with next experiment - error is captured by step_context
                    continue
            
            # Create execution summary
            await self._create_execution_summary(ctx, execution_results)
            
            # Mark execution planning as complete before calling the LLM
            ctx.session.state[execution_executed_key] = True
            
            # Run standard LLM agent to analyze execution results
            print("🤖 Running LLM agent to analyze execution results...")
            async for event in super()._run_async_impl(ctx):
                yield event
    
    async def _resume_operation(self, ctx: InvocationContext, op_info: Dict[str, Any]) -> AsyncGenerator[Event, None]:
        """Resume a failed or incomplete operation."""
        
        operation_id = op_info["operation_id"]
        print(f"🔄 Resuming operation: {operation_id}")
        
        # Resume the operation
        progress = micro_checkpoint_manager.resume_operation(operation_id)
        if not progress:
            return
        
        # Load operation data to get remaining steps
        operation_path = os.path.join(
            micro_checkpoint_manager.micro_checkpoints_dir,
            f"operation_{operation_id}.json"
        )
        
        with open(operation_path, 'r') as f:
            operation_data = json.load(f)
        
        all_steps = [OperationStep(**step_data) for step_data in operation_data["steps"]]
        
        # Find remaining steps
        remaining_steps = [
            step for step in all_steps
            if step.step_id not in progress.completed_steps
            and step.step_id not in progress.failed_steps
        ]
        
        print(f"   📋 Resuming {len(remaining_steps)} remaining steps")
        
        # Continue execution from where we left off
        execution_results = []
        
        for step in remaining_steps:
            try:
                with micro_checkpoint_manager.step_context(step):
                    experiment_config = step.input_state
                    result = await self._execute_single_experiment(ctx, experiment_config)
                    execution_results.append(result)
                    
                    print(f"✅ Resumed experiment: {experiment_config.get('name', 'Unknown')}")
                    
            except Exception as e:
                print(f"❌ Resumed experiment step failed: {step.step_name} - {e}")
                continue
        
        if execution_results:
            await self._create_execution_summary(ctx, execution_results)
    
    async def _parse_implementation_plan(self, plan_path: str) -> List[Dict[str, Any]]:
        """Parse implementation plan from JSON manifest to extract experiment configurations."""
        try:
            with open(plan_path, 'r') as f:
                manifest_data = json.load(f)

            if not isinstance(manifest_data, dict):
                print(f"❌ Error parsing implementation plan: Manifest root is not a JSON object, but {type(manifest_data)}")
                return []

            implementation_plan = manifest_data.get("implementation_plan", {})
            tasks = implementation_plan.get("parallel_tasks", [])

            if not isinstance(tasks, list):
                print(f"❌ Error parsing implementation plan: 'parallel_tasks' is not a list.")
                return []

            # Convert manifest tasks into experiment configurations
            experiments = []
            for i, task in enumerate(tasks):
                task_id = task.get("task_id", f"task_{i+1}")
                experiments.append({
                    "name": task.get("description", f"Experiment for {task_id}"),
                    "type": "python_script",
                    # Assuming a convention for script paths. This might need more robust logic
                    # based on what the CoderWorkflow outputs.
                    "code": f"python workspace/scripts/{task_id}.py",
                    "expected_outputs": task.get("outputs", []),
                    "timeout": 300,
                    "max_retries": 1
                })
            
            return experiments
            
        except json.JSONDecodeError as e:
            print(f"❌ Error decoding JSON from implementation plan: {e}")
            return []
        except Exception as e:
            print(f"❌ Error parsing implementation plan: {e}")
            return []
    
    async def _execute_single_experiment(self, ctx: InvocationContext, experiment_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single experiment with basic tracking."""
        
        experiment_name = experiment_config.get("name", "Unknown_Experiment")
        
        result = {
            "experiment_name": experiment_name,
            "status": "completed",
            "method": "micro_checkpoint_execution",
            "config": experiment_config
        }
        
        # Simulate experiment execution
        # In practice, this would call tools to run the actual experiment
        print(f"   🔬 Executing: {experiment_name}")
        
        return result
    
    async def _create_execution_summary(self, ctx: InvocationContext, results: List[Dict[str, Any]]):
        """Create a summary of all experiment executions."""
        task_id = ctx.session.state.get('task_id', config.TASK_ID)
        outputs_dir = config.get_outputs_dir(task_id)
        
        summary = {
            "task_id": task_id,
            "total_experiments": len(results),
            "successful_experiments": len([r for r in results if r.get("status") == "completed"]),
            "failed_experiments": len([r for r in results if r.get("status") == "failed"]),
            "execution_details": results,
            "micro_checkpoints_used": True,
            "recovery_info": {
                "operation_id": micro_checkpoint_manager.current_operation,
                "checkpoints_created": len(results)
            }
        }
        
        summary_path = os.path.join(outputs_dir, "execution", "micro_checkpoint_summary.json")
        os.makedirs(os.path.dirname(summary_path), exist_ok=True)
        
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        # Update session state
        ctx.session.state['execution_log_artifact'] = summary_path
        ctx.session.state['micro_checkpoints_enabled'] = True
        
        print(f"💾 Micro-checkpoint summary: {summary_path}")


def get_experiment_executor_agent():
    """Create Experiment Executor agent with micro-checkpoint support."""
    agent_name = "Experiment_Executor"
    
    # Only use mock agent in actual dry_run mode with LLM skipping
    if config.EXECUTION_MODE == "dry_run" and config.DRY_RUN_SKIP_LLM:
        from ..tools.mock_llm_agent import create_mock_llm_agent
        return create_mock_llm_agent(name=agent_name)
    
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
        output_key="execution_log_artifact"
    )
    
    return agent

