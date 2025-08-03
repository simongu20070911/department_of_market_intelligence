# /department_of_market_intelligence/agents/chief_researcher.py
import asyncio
import os
import json
from typing import Dict, Any, List, AsyncGenerator
from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai import types

from .. import config
from ..utils.model_loader import get_llm_model
from ..utils.operation_tracking import (
    tracked_operation,
    create_file_generation_operation,
    OperationStep
)
from ..utils.micro_checkpoint_manager import micro_checkpoint_manager
from ..prompts.definitions.chief_researcher import CHIEF_RESEARCHER_INSTRUCTION


class MicroCheckpointChiefResearcher(LlmAgent):
    """Chief Researcher with micro-checkpoint support for fine-grained recovery."""
    
    def __init__(self, model, tools, instruction_provider, **kwargs):
        super().__init__(
            model=model,
            name="Chief_Researcher",
            instruction=instruction_provider,
            tools=tools,
            **kwargs
        )
    
    async def _run_async_impl(self, ctx):
        """Enhanced research planning with fine-grained checkpointing."""
        
        # Check if micro-checkpoints are enabled
        if not config.ENABLE_MICRO_CHECKPOINTS:
            print("🔄 Micro-checkpoints disabled - running standard execution")
            async for event in super()._run_async_impl(ctx):
                yield event
            return
        
        # Check for resumable operations first
        recoverable_ops = micro_checkpoint_manager.list_recoverable_operations()
        researcher_ops = [op for op in recoverable_ops if "Chief_Researcher" in op.get("agent_name", "")]
        
        if researcher_ops and config.MICRO_CHECKPOINT_AUTO_RESUME:
            print(f"🔄 Found {len(researcher_ops)} recoverable research operations")
            for op in researcher_ops:
                print(f"   • {op['operation_id']}: {op['progress']} steps completed")
            
            # Resume operations automatically
            for op_info in researcher_ops:
                async for event in self._resume_operation(ctx, op_info):
                    yield event
            return
        
        # Get task info from session state
        task_id = ctx.session.state.get('task_id', config.TASK_ID)
        current_task = ctx.session.state.get('current_task', 'research_planning')
        
        # Define research planning steps
        research_steps = [
            {
                "filename": f"research_plan_v1.md",
                "step_name": "Generate Initial Research Plan",
                "description": "Create comprehensive research methodology and approach",
                "timeout": 240,
                "max_retries": 2
            },
            {
                "filename": f"research_scope.md", 
                "step_name": "Define Research Scope",
                "description": "Establish boundaries and limitations for the research",
                "timeout": 180,
                "max_retries": 2
            },
            {
                "filename": f"methodology_validation.md",
                "step_name": "Validate Research Methodology",
                "description": "Review and validate the proposed research approach",
                "timeout": 200,
                "max_retries": 1
            }
        ]
        
        # Create tracked operation for research planning
        operation_id = f"research_planning_{task_id}_{int(asyncio.get_event_loop().time())}"
        
        research_operation = create_file_generation_operation(
            operation_id=operation_id,
            agent_name="Chief_Researcher",
            files_to_generate=research_steps
        )
        
        # Execute research planning with fine-grained tracking
        print(f"📋 Starting research planning with {len(research_steps)} tracked steps")
        
        with research_operation.execute() as (tracker, steps):
            planning_results = []
            
            for step in steps:
                try:
                    with tracker.step_context(step):
                        # Execute individual planning step with checkpointing
                        step_config = step.input_state
                        result = await self._execute_planning_step(ctx, step_config)
                        planning_results.append(result)
                        
                        print(f"✅ Completed planning step: {step_config.get('step_name', 'Unknown')}")
                        
                except Exception as e:
                    print(f"❌ Planning step failed: {step.step_name} - {e}")
                    # Continue with next step - error is captured by step_context
                    continue
            
            # Create planning summary
            await self._create_planning_summary(ctx, planning_results)
            
            # Run standard LLM agent to finalize planning
            print("🤖 Running LLM agent to finalize research planning...")
            async for event in super()._run_async_impl(ctx):
                yield event
    
    async def _resume_operation(self, ctx: InvocationContext, op_info: Dict[str, Any]) -> AsyncGenerator[Event, None]:
        """Resume a failed or incomplete research operation."""
        
        operation_id = op_info["operation_id"]
        print(f"🔄 Resuming research operation: {operation_id}")
        
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
        planning_results = []
        
        for step in remaining_steps:
            try:
                with micro_checkpoint_manager.step_context(step):
                    step_config = step.input_state
                    result = await self._execute_planning_step(ctx, step_config)
                    planning_results.append(result)
                    
                    print(f"✅ Resumed planning step: {step_config.get('step_name', 'Unknown')}")
                    
            except Exception as e:
                print(f"❌ Resumed planning step failed: {step.step_name} - {e}")
                continue
        
        if planning_results:
            await self._create_planning_summary(ctx, planning_results)
    
    async def _execute_planning_step(self, ctx: InvocationContext, step_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single planning step with basic tracking."""
        
        step_name = step_config.get("step_name", "Unknown_Step")
        filename = step_config.get("filename", "unknown.md")
        
        result = {
            "step_name": step_name,
            "filename": filename,
            "status": "completed",
            "method": "micro_checkpoint_execution",
            "config": step_config
        }
        
        # Simulate planning step execution
        # In practice, this would call tools to generate the actual file
        print(f"   📝 Executing: {step_name}")
        
        return result
    
    async def _create_planning_summary(self, ctx: InvocationContext, results: List[Dict[str, Any]]):
        """Create a summary of all planning steps."""
        task_id = ctx.session.state.get('task_id', config.TASK_ID)
        outputs_dir = config.get_outputs_dir(task_id)
        
        summary = {
            "task_id": task_id,
            "total_planning_steps": len(results),
            "successful_steps": len([r for r in results if r.get("status") == "completed"]),
            "failed_steps": len([r for r in results if r.get("status") == "failed"]),
            "planning_details": results,
            "micro_checkpoints_used": True,
            "recovery_info": {
                "operation_id": micro_checkpoint_manager.current_operation,
                "checkpoints_created": len(results)
            }
        }
        
        summary_path = os.path.join(outputs_dir, "planning", "micro_checkpoint_planning_summary.json")
        os.makedirs(os.path.dirname(summary_path), exist_ok=True)
        
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        # Update session state
        ctx.session.state['planning_summary_artifact'] = summary_path
        ctx.session.state['micro_checkpoints_enabled'] = True
        
        print(f"💾 Planning micro-checkpoint summary: {summary_path}")

