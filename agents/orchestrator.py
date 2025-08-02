# /department_of_market_intelligence/agents/orchestrator.py
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
    create_data_processing_operation,
    OperationStep
)
from ..utils.micro_checkpoint_manager import micro_checkpoint_manager
from ..prompts.definitions.orchestrator import ORCHESTRATOR_INSTRUCTION


class MicroCheckpointOrchestrator(LlmAgent):
    """Orchestrator with micro-checkpoint support for fine-grained recovery."""
    
    def __init__(self, model, tools, instruction_provider):
        super().__init__(
            model=model,
            name="Orchestrator",
            instruction=instruction_provider,
            tools=tools,
            after_model_callback=ensure_end_of_output
        )
    
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """Enhanced orchestration with fine-grained checkpointing."""
        
        # Check if micro-checkpoints are enabled
        if not config.ENABLE_MICRO_CHECKPOINTS:
            print("🔄 Micro-checkpoints disabled - running standard execution")
            async for event in super()._run_async_impl(ctx):
                yield event
            return
        
        # Check for resumable operations first
        recoverable_ops = micro_checkpoint_manager.list_recoverable_operations()
        orchestrator_ops = [op for op in recoverable_ops if "Orchestrator" in op.get("agent_name", "")]
        
        if orchestrator_ops and config.MICRO_CHECKPOINT_AUTO_RESUME:
            print(f"🔄 Found {len(orchestrator_ops)} recoverable orchestration operations")
            for op in orchestrator_ops:
                print(f"   • {op['operation_id']}: {op['progress']} steps completed")
            
            # Resume operations automatically
            for op_info in orchestrator_ops:
                async for event in self._resume_operation(ctx, op_info):
                    yield event
            return
        
        # Get task info from session state
        task_id = ctx.session.state.get('task_id', config.TASK_ID)
        current_task = ctx.session.state.get('current_task', 'orchestration')
        
        # Define orchestration steps
        orchestration_steps = [
            {
                "name": "Parse Research Plan",
                "description": "Parse and understand the research plan requirements",
                "expected_outputs": ["parsed_requirements.json"],
                "timeout": 180,
                "max_retries": 2
            },
            {
                "name": "Generate Implementation Strategy",
                "description": "Create detailed implementation strategy from research plan",
                "expected_outputs": ["implementation_strategy.md"],
                "timeout": 240,
                "max_retries": 2
            },
            {
                "name": "Create Execution Graph",
                "description": "Generate parallel execution graph for experiments",
                "expected_outputs": ["execution_graph.json"],
                "timeout": 200,
                "max_retries": 1
            },
            {
                "name": "Validate Dependencies",
                "description": "Validate all dependencies and prerequisites",
                "expected_outputs": ["dependency_validation.json"],
                "timeout": 150,
                "max_retries": 1
            }
        ]
        
        # Create tracked operation for orchestration
        operation_id = f"orchestration_{task_id}_{int(asyncio.get_event_loop().time())}"
        
        orchestration_operation = create_data_processing_operation(
            operation_id=operation_id,
            agent_name="Orchestrator",
            processing_steps=orchestration_steps
        )
        
        # Execute orchestration with fine-grained tracking
        print(f"🎯 Starting orchestration with {len(orchestration_steps)} tracked steps")
        
        with orchestration_operation.execute() as (tracker, steps):
            orchestration_results = []
            
            for step in steps:
                try:
                    with tracker.step_context(step):
                        # Execute individual orchestration step with checkpointing
                        step_config = step.input_state
                        result = await self._execute_orchestration_step(ctx, step_config)
                        orchestration_results.append(result)
                        
                        print(f"✅ Completed orchestration step: {step_config.get('name', 'Unknown')}")
                        
                except Exception as e:
                    print(f"❌ Orchestration step failed: {step.step_name} - {e}")
                    # Continue with next step - error is captured by step_context
                    continue
            
            # Create orchestration summary
            await self._create_orchestration_summary(ctx, orchestration_results)
            
            # Run standard LLM agent to finalize orchestration
            print("🤖 Running LLM agent to finalize orchestration...")
            async for event in super()._run_async_impl(ctx):
                yield event
    
    async def _resume_operation(self, ctx: InvocationContext, op_info: Dict[str, Any]) -> AsyncGenerator[Event, None]:
        """Resume a failed or incomplete orchestration operation."""
        
        operation_id = op_info["operation_id"]
        print(f"🔄 Resuming orchestration operation: {operation_id}")
        
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
        orchestration_results = []
        
        for step in remaining_steps:
            try:
                with micro_checkpoint_manager.step_context(step):
                    step_config = step.input_state
                    result = await self._execute_orchestration_step(ctx, step_config)
                    orchestration_results.append(result)
                    
                    print(f"✅ Resumed orchestration step: {step_config.get('name', 'Unknown')}")
                    
            except Exception as e:
                print(f"❌ Resumed orchestration step failed: {step.step_name} - {e}")
                continue
        
        if orchestration_results:
            await self._create_orchestration_summary(ctx, orchestration_results)
    
    async def _execute_orchestration_step(self, ctx: InvocationContext, step_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single orchestration step with basic tracking."""
        
        step_name = step_config.get("name", "Unknown_Step")
        
        result = {
            "step_name": step_name,
            "description": step_config.get("description", ""),
            "status": "completed",
            "method": "micro_checkpoint_execution",
            "expected_outputs": step_config.get("expected_outputs", []),
            "config": step_config
        }
        
        # Simulate orchestration step execution
        # In practice, this would call tools to perform the actual orchestration
        print(f"   🎯 Executing: {step_name}")
        
        return result
    
    async def _create_orchestration_summary(self, ctx: InvocationContext, results: List[Dict[str, Any]]):
        """Create a summary of all orchestration steps."""
        task_id = ctx.session.state.get('task_id', config.TASK_ID)
        outputs_dir = config.get_outputs_dir(task_id)
        
        summary = {
            "task_id": task_id,
            "total_orchestration_steps": len(results),
            "successful_steps": len([r for r in results if r.get("status") == "completed"]),
            "failed_steps": len([r for r in results if r.get("status") == "failed"]),
            "orchestration_details": results,
            "micro_checkpoints_used": True,
            "recovery_info": {
                "operation_id": micro_checkpoint_manager.current_operation,
                "checkpoints_created": len(results)
            }
        }
        
        summary_path = os.path.join(outputs_dir, "implementation", "micro_checkpoint_orchestration_summary.json")
        os.makedirs(os.path.dirname(summary_path), exist_ok=True)
        
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        # Update session state
        ctx.session.state['orchestration_summary_artifact'] = summary_path
        ctx.session.state['micro_checkpoints_enabled'] = True
        
        print(f"💾 Orchestration micro-checkpoint summary: {summary_path}")


def get_orchestrator_agent():
    """Creates Orchestrator agent with micro-checkpoint support."""
    # Use the centralized toolset registry
    from ..tools.toolset_registry import toolset_registry
    desktop_commander_toolset = toolset_registry.get_desktop_commander_toolset()
    
    # Wrap in list if it's a real MCP toolset, mock tools are already a list
    if toolset_registry.is_using_real_mcp():
        tools = [desktop_commander_toolset]
    else:
        tools = desktop_commander_toolset
        
    # Create instruction provider for dynamic template variable injection with context pre-loading
    def instruction_provider(ctx: ReadonlyContext) -> str:
        from ..prompts.builder import inject_template_variables_with_context_preloading
        return inject_template_variables_with_context_preloading(ORCHESTRATOR_INSTRUCTION, ctx, "Orchestrator")
    
    # Return the micro-checkpoint enabled orchestrator
    return MicroCheckpointOrchestrator(
        model=get_llm_model(config.ORCHESTRATOR_MODEL),
        tools=tools,
        instruction_provider=instruction_provider
    )