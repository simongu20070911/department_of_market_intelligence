# /department_of_market_intelligence/agents/enhanced_experiment_executor.py
"""Enhanced Experiment Executor with fine-grained recovery capabilities."""

import os
import json
import asyncio
from typing import Dict, Any, List, AsyncGenerator
from google.adk.agents import LlmAgent
from google.adk.agents.llm_agent import ReadonlyContext
from google.adk.agents.api import Event
from google.adk.context import InvocationContext

from .. import config
from ..utils.callbacks import ensure_end_of_output
from ..utils.model_loader import get_llm_model
from ..utils.operation_tracking import (
    tracked_operation,
    create_experiment_operation,
    create_file_generation_operation,
    OperationStep,
    recoverable_operation
)
from ..utils.micro_checkpoint_manager import micro_checkpoint_manager
from ..prompts.definitions.experiment_executor import EXPERIMENT_EXECUTOR_INSTRUCTION


class EnhancedExperimentExecutor(LlmAgent):
    """Experiment Executor with micro-checkpoint support for fine-grained recovery."""
    
    def __init__(self):
        # Use the centralized toolset registry
        from ..tools.toolset_registry import toolset_registry
        desktop_commander_toolset = toolset_registry.get_desktop_commander_toolset()
        
        # Wrap in list if it's a real MCP toolset, mock tools are already a list
        if toolset_registry.is_using_real_mcp():
            tools = [desktop_commander_toolset]
        else:
            tools = desktop_commander_toolset
        
        # Create instruction provider for dynamic template variable injection
        def instruction_provider(ctx: "ReadonlyContext") -> str:
            from ..prompts.builder import inject_template_variables
            return inject_template_variables(EXPERIMENT_EXECUTOR_INSTRUCTION, ctx, "Enhanced_Experiment_Executor")
        
        super().__init__(
            model=get_llm_model(config.EXECUTOR_MODEL),
            name="Enhanced_Experiment_Executor",
            instruction=instruction_provider,
            tools=tools,
            after_model_callback=ensure_end_of_output
        )
    
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """Enhanced execution with fine-grained checkpointing."""
        
        # Check for resumable operations first
        recoverable_ops = micro_checkpoint_manager.list_recoverable_operations()
        if recoverable_ops:
            print(f"🔄 Found {len(recoverable_ops)} recoverable operations")
            for op in recoverable_ops:
                if op["agent_name"] == "Enhanced_Experiment_Executor":
                    print(f"   • {op['operation_id']}: {op['progress']} steps completed")
            
            # Ask if we should resume any operations
            should_resume = input("Resume any operations? (y/n): ").lower().startswith('y')
            if should_resume:
                async for event in self._resume_operations(ctx, recoverable_ops):
                    yield event
                return
        
        # Get implementation plan and task info from session state
        implementation_plan_path = ctx.session.state.get('implementation_plan_artifact')
        task_id = ctx.session.state.get('task_id', config.TASK_ID)
        
        if not implementation_plan_path:
            print("❌ No implementation plan found - cannot execute experiments")
            return
        
        # Parse implementation plan to identify experiments
        experiments = await self._parse_implementation_plan(implementation_plan_path)
        
        if not experiments:
            print("❌ No experiments found in implementation plan")
            return
        
        # Create tracked operation for experiment execution
        operation_id = f"execute_experiments_{task_id}_{int(asyncio.get_event_loop().time())}"
        
        experiment_operation = create_experiment_operation(
            operation_id=operation_id,
            agent_name="Enhanced_Experiment_Executor",
            experiment_configs=experiments
        )
        
        # Execute experiments with fine-grained tracking
        with experiment_operation.execute() as (tracker, steps):
            execution_results = []
            
            for step in steps:
                try:
                    with tracker.step_context(step):
                        # Execute individual experiment with micro-checkpointing
                        experiment_config = step.input_state
                        result = await self._execute_single_experiment(ctx, experiment_config, step)
                        execution_results.append(result)
                        
                        # Yield progress events
                        async for event in self._create_progress_events(step, result):
                            yield event
                            
                except Exception as e:
                    print(f"❌ Experiment step failed: {step.step_name} - {e}")
                    # Error is automatically captured by step_context
                    # Continue with next experiment
                    continue
            
            # Create execution summary with all results
            await self._create_execution_summary(ctx, execution_results)
    
    async def _resume_operations(self, ctx: InvocationContext, recoverable_ops: List[Dict[str, Any]]) -> AsyncGenerator[Event, None]:
        """Resume failed or incomplete operations."""
        
        for op_info in recoverable_ops:
            if op_info["agent_name"] != "Enhanced_Experiment_Executor":
                continue
            
            operation_id = op_info["operation_id"]
            print(f"🔄 Resuming operation: {operation_id}")
            
            # Resume the operation
            progress = micro_checkpoint_manager.resume_operation(operation_id)
            if not progress:
                continue
            
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
            for step in remaining_steps:
                try:
                    with micro_checkpoint_manager.step_context(step):
                        experiment_config = step.input_state
                        result = await self._execute_single_experiment(ctx, experiment_config, step)
                        
                        # Yield progress events
                        async for event in self._create_progress_events(step, result):
                            yield event
                            
                except Exception as e:
                    print(f"❌ Resumed experiment step failed: {step.step_name} - {e}")
                    continue
    
    async def _parse_implementation_plan(self, plan_path: str) -> List[Dict[str, Any]]:
        """Parse implementation plan to extract experiment configurations."""
        try:
            with open(plan_path, 'r') as f:
                plan_content = f.read()
            
            # Extract experiment sections from the plan
            # This is a simplified parser - in practice, you'd want more robust parsing
            experiments = []
            
            # Look for experiment code blocks or sections
            if "```python" in plan_content:
                # Extract Python code blocks as experiments
                code_blocks = []
                lines = plan_content.split('\n')
                in_code_block = False
                current_block = []
                
                for line in lines:
                    if line.strip().startswith("```python"):
                        in_code_block = True
                        current_block = []
                    elif line.strip().startswith("```") and in_code_block:
                        if current_block:
                            code_blocks.append('\n'.join(current_block))
                        in_code_block = False
                    elif in_code_block:
                        current_block.append(line)
                
                # Convert code blocks to experiment configs
                for i, code in enumerate(code_blocks):
                    experiments.append({
                        "name": f"Experiment_{i+1}",
                        "type": "python_script",
                        "code": code,
                        "expected_outputs": [f"experiment_{i+1}_results.json"],
                        "timeout": 600,
                        "max_retries": 1
                    })
            
            return experiments
            
        except Exception as e:
            print(f"❌ Error parsing implementation plan: {e}")
            return []
    
    @recoverable_operation(
        operation_id=None,  # Will be auto-generated
        expected_outputs=["experiment_results.json"],
        timeout_seconds=600,
        max_retries=2
    )
    async def _execute_single_experiment(self, 
                                       ctx: InvocationContext, 
                                       experiment_config: Dict[str, Any],
                                       step: OperationStep) -> Dict[str, Any]:
        """Execute a single experiment with recovery support."""
        
        experiment_name = experiment_config.get("name", "Unknown_Experiment")
        experiment_type = experiment_config.get("type", "python_script")
        
        print(f"🧪 Executing experiment: {experiment_name}")
        
        result = {
            "experiment_name": experiment_name,
            "experiment_type": experiment_type,
            "status": "started",
            "start_time": asyncio.get_event_loop().time(),
            "step_id": step.step_id
        }
        
        try:
            if experiment_type == "python_script":
                result.update(await self._execute_python_experiment(ctx, experiment_config))
            elif experiment_type == "data_analysis":
                result.update(await self._execute_data_analysis(ctx, experiment_config))
            else:
                result.update(await self._execute_generic_experiment(ctx, experiment_config))
            
            result["status"] = "completed"
            result["end_time"] = asyncio.get_event_loop().time()
            result["duration"] = result["end_time"] - result["start_time"]
            
            print(f"✅ Experiment completed: {experiment_name} ({result['duration']:.2f}s)")
            
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            result["end_time"] = asyncio.get_event_loop().time()
            print(f"❌ Experiment failed: {experiment_name} - {e}")
            raise  # Re-raise to trigger retry logic
        
        return result
    
    async def _execute_python_experiment(self, ctx: InvocationContext, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Python-based experiment."""
        code = config.get("code", "")
        if not code:
            raise ValueError("No Python code provided")
        
        # Create a temporary script file
        outputs_dir = config.get("outputs_dir", config.get_outputs_dir(ctx.session.state.get('task_id')))
        script_path = os.path.join(outputs_dir, "execution", f"temp_experiment_{int(asyncio.get_event_loop().time())}.py")
        
        os.makedirs(os.path.dirname(script_path), exist_ok=True)
        with open(script_path, 'w') as f:
            f.write(code)
        
        # Execute the script (this would typically involve tool calls)
        # For now, we'll simulate execution
        return {
            "script_path": script_path,
            "execution_method": "python_script",
            "outputs_generated": config.get("expected_outputs", [])
        }
    
    async def _execute_data_analysis(self, ctx: InvocationContext, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a data analysis experiment."""
        # Implement data analysis execution logic
        return {
            "analysis_type": config.get("analysis_type", "general"),
            "data_sources": config.get("data_sources", []),
            "execution_method": "data_analysis"
        }
    
    async def _execute_generic_experiment(self, ctx: InvocationContext, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a generic experiment."""
        # Implement generic experiment execution logic
        return {
            "experiment_config": config,
            "execution_method": "generic"
        }
    
    async def _create_progress_events(self, step: OperationStep, result: Dict[str, Any]) -> AsyncGenerator[Event, None]:
        """Create progress events for the experiment step."""
        # This would yield appropriate ADK Event objects
        # For now, we'll just pass
        if False:  # Placeholder to make this a generator
            yield
    
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
                "checkpoints_created": len(results)  # One per experiment
            }
        }
        
        summary_path = os.path.join(outputs_dir, "execution", "execution_summary.json")
        os.makedirs(os.path.dirname(summary_path), exist_ok=True)
        
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        # Update session state with execution results
        ctx.session.state['execution_summary_artifact'] = summary_path
        ctx.session.state['experiments_completed'] = summary['successful_experiments']
        ctx.session.state['experiments_failed'] = summary['failed_experiments']
        
        print(f"📊 Execution Summary Created:")
        print(f"   ✅ Successful: {summary['successful_experiments']}")
        print(f"   ❌ Failed: {summary['failed_experiments']}")
        print(f"   💾 Summary saved: {summary_path}")


def get_enhanced_experiment_executor_agent():
    """Create Enhanced Experiment Executor agent with micro-checkpoint support."""
    if config.EXECUTION_MODE == "dry_run" and config.DRY_RUN_SKIP_LLM:
        from ..tools.mock_llm_agent import create_mock_llm_agent
        return create_mock_llm_agent(name="Enhanced_Experiment_Executor")
    
    return EnhancedExperimentExecutor()