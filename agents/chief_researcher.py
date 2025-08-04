# /department_of_market_intelligence/agents/chief_researcher.py
import asyncio
import os
import json
from typing import Dict, Any, List, AsyncGenerator
from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event

from .. import config
from ..utils.callbacks import ensure_end_of_output
from ..utils.model_loader import get_llm_model
from ..utils.operation_tracking import (
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
        
        # Use a unique key to track if this pre-planning has been done for the current task version
        plan_version = ctx.session.state.get('plan_version', 0)
        task_id = ctx.session.state.get('task_id', config.TASK_ID)
        planning_executed_key = f"chief_researcher_planning_executed_v{plan_version}_for_{task_id}"

        if ctx.session.state.get(planning_executed_key):
            print("🔄 Micro-checkpoint planning already completed for this version. Running LLM agent directly.")
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
        outputs_dir = config.get_outputs_dir(task_id)
        
        # Define research planning steps
        research_steps = [
            {
                "filename": f"{outputs_dir}/planning/research_plan_v{plan_version}.md",
                "step_name": "Generate Initial Research Plan",
                "description": "Create a comprehensive research methodology and approach based on the main task. This should be the core document.",
                "timeout": 240,
                "max_retries": 2
            },
            {
                "filename": f"{outputs_dir}/planning/research_scope_v{plan_version}.md", 
                "step_name": "Define Research Scope",
                "description": "Establish clear boundaries, limitations, and out-of-scope items for the research to ensure focus.",
                "timeout": 180,
                "max_retries": 2
            },
            {
                "filename": f"{outputs_dir}/planning/methodology_validation_plan_v{plan_version}.md",
                "step_name": "Plan for Methodology Validation",
                "description": "Outline the specific steps and criteria that will be used to review and validate the proposed research approach, including statistical tests and data hygiene checks.",
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
            
            # Mark this version of planning as complete before calling the LLM
            ctx.session.state[planning_executed_key] = True
            
            # Run standard LLM agent to synthesize and finalize the research plan
            print("🤖 Running LLM agent to synthesize and finalize research planning...")
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

        # FIX: Add a check to halt if the resumed operation has failed steps.
        # This prevents the agent from proceeding with a broken state.
        progress = micro_checkpoint_manager.operation_registry.get(operation_id)
        if progress and progress.failed_steps:
            print(f"❌ CRITICAL: Resumed operation '{operation_id}' has {len(progress.failed_steps)} failed steps. Halting.")
            # Stop the generator, effectively halting this agent's execution.
            return

        # After resuming, run the final synthesis step
        print("🤖 Running LLM agent to synthesize and finalize resumed research planning...")
        async for event in super()._run_async_impl(ctx):
            yield event
    
    async def _execute_planning_step(self, ctx: InvocationContext, step_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single, real planning step by generating a file."""
        from ..utils.task_loader import load_task_description
        task_id = ctx.session.state.get('task_id', config.TASK_ID)
        task_description = load_task_description(task_id)

        prompt_template = f"""
        You are the Chief Researcher. Your current high-level task is:
        ---
        {task_description}
        ---
        You are now performing one specific sub-step of the planning phase.
        
        Sub-step Name: {step_config['step_name']}
        Sub-step Goal: {step_config['description']}
        
        Generate the complete and detailed markdown content for the document: `{os.path.basename(step_config['filename'])}`.
        Your response must ONLY be the raw markdown content for this file. Do not include any other commentary, greetings, or explanations.
        """
        return await self._execute_step_with_llm(ctx, step_config, prompt_template)

    def _find_tool(self, tool_name: str):
        """Finds a tool by name from the agent's tool list."""
        for tool in self.tools:
            # Check if it's a regular tool with a name attribute
            if hasattr(tool, 'name') and tool.name == tool_name:
                return tool
            # Handle MCPToolset case
            if hasattr(tool, 'get_tools'):
                for mcp_tool in tool.get_tools():
                    if mcp_tool.name.endswith(f"__{tool_name}"):
                        return mcp_tool
        raise ValueError(f"Tool '{tool_name}' not found in agent's toolset.")

    async def _execute_step_with_llm(self, ctx: InvocationContext, step_config: Dict[str, Any], prompt: str) -> Dict[str, Any]:
        """Generic helper to execute a step that generates a file via LLM."""
        from google.genai.types import Content, Part

        step_name = step_config.get("step_name", "Unknown_Step")
        filename = step_config.get("filename", "unknown.md")
        
        print(f"   🧠 Generating content for: {step_name}")
        
        # --- FIX: Use the standard ADK method for calling the model ---
        request_content = Content(parts=[Part(text=prompt)])
        content_to_write = ""
        
        # The generate_content_async method returns a stream of LlmResponse objects
        async for llm_response in self.model.generate_content_async(request_content):
            if llm_response.text:
                content_to_write += llm_response.text
        
        content_to_write = content_to_write.strip()
        # --- END FIX ---

        # Clean up markdown code blocks if the model wraps the output
        if content_to_write.startswith("```markdown"):
            content_to_write = content_to_write.split('\n', 1)[1]
            if content_to_write.endswith("```"):
                content_to_write = content_to_write[:-3].strip()

        # Write the content to the specified file using the agent's tool
        print(f"   ✍️ Writing content to: {filename}")
        write_tool = self._find_tool("write_file")
        
        # --- FIX: Correctly iterate over the async generator from run_async ---
        tool_event_generator = write_tool.run_async(
            args={'path': filename, 'content': content_to_write},
            tool_context=None # Note: This context is None, which might be a limitation for complex tools
        )
        
        # Consume the generator to ensure the tool call completes
        async for _ in tool_event_generator:
            pass
        # --- END FIX ---

        return {
            "step_name": step_name,
            "filename": filename,
            "status": "completed",
            "method": "micro_checkpoint_execution",
            "config": step_config
        }
    
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


def get_chief_researcher_agent():
    """Create Chief Researcher agent with micro-checkpoint support."""
    agent_name = "Chief_Researcher"
    
    # Only use mock agent in actual dry_run mode with LLM skipping
    if config.EXECUTION_MODE == "dry_run" and config.DRY_RUN_SKIP_LLM:
        from ..tools.mock_llm_agent import create_mock_llm_agent
        return create_mock_llm_agent(name=agent_name)
    
    # Get tools from the registry
    from ..tools.toolset_registry import toolset_registry
    desktop_commander_toolset = toolset_registry.get_desktop_commander_toolset()
    
    # Wrap in list if it's a real MCP toolset, mock tools are already a list
    tools = [desktop_commander_toolset] if toolset_registry.is_using_real_mcp() else desktop_commander_toolset
    
    def instruction_provider(ctx=None) -> str:
        from ..prompts.builder import inject_template_variables_with_context_preloading
        return inject_template_variables_with_context_preloading(CHIEF_RESEARCHER_INSTRUCTION, ctx, agent_name)
    
    agent = MicroCheckpointChiefResearcher(
        model=get_llm_model(config.CHIEF_RESEARCHER_MODEL),
        instruction_provider=instruction_provider,
        tools=tools,
        after_model_callback=ensure_end_of_output,
        output_key="plan_artifact_name"
    )
    
    return agent