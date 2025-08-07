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
from ..utils.state_adapter import get_domi_state
from ..utils.checkpoint_manager import CheckpointManager, TrackedOperation
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
        domi_state = get_domi_state(ctx)
        task_id = domi_state.task_id
        checkpoint_manager = CheckpointManager(task_id)

        # Check if micro-checkpoints are enabled
        if not config.ENABLE_MICRO_CHECKPOINTS:
            print("[Chief_Researcher]: Micro-checkpoints disabled, running standard execution.")
            async for event in super()._run_async_impl(ctx):
                yield event
            return
        
        plan_version = domi_state.validation.validation_version
        planning_executed_key = f"chief_researcher_planning_executed_v{plan_version}_for_{task_id}"

        if domi_state.metadata.get(planning_executed_key):
            print(f"[Chief_Researcher]: Micro-checkpoint planning already completed for version {plan_version}. Running LLM agent directly.")
            async for event in super()._run_async_impl(ctx):
                yield event
            return
        
        # Check for resumable operations
        recoverable_ops = checkpoint_manager.list_recoverable_operations(agent_name="Chief_Researcher")
        
        current_task = domi_state.current_task_description
        if recoverable_ops and config.MICRO_CHECKPOINT_AUTO_RESUME and current_task != 'refine_plan':
            print(f"[Chief_Researcher]: Found {len(recoverable_ops)} recoverable research operations. Resuming...")
            for op_info in recoverable_ops:
                operation = checkpoint_manager.resume_operation(op_info['operation_id'])
                if operation:
                    await self._execute_tracked_operation(ctx, operation)
            return
        elif current_task == 'refine_plan' and recoverable_ops:
            print(f"[Chief_Researcher]: Starting fresh for revision v{plan_version}, cleaning up old operations.")
            for op in recoverable_ops:
                checkpoint_manager.mark_operation_complete(op['operation_id'])
        
        if current_task == 'refine_plan':
            print(f"[Chief_Researcher]: Refining plan to version {plan_version} based on validation feedback.")
            async for event in super()._run_async_impl(ctx):
                yield event
            return
        
        outputs_dir = config.get_outputs_dir(task_id)
        research_steps = [
            {"step_name": "Generate Initial Research Plan", "input_state": {"filename": f"{outputs_dir}/planning/research_plan_v{plan_version}.md", "description": "Create a comprehensive research methodology..."}},
            {"step_name": "Define Research Scope", "input_state": {"filename": f"{outputs_dir}/planning/research_scope_v{plan_version}.md", "description": "Establish clear boundaries and limitations..."}},
            {"step_name": "Plan for Methodology Validation", "input_state": {"filename": f"{outputs_dir}/planning/methodology_validation_plan_v{plan_version}.md", "description": "Outline steps to validate the research approach..."}},
        ]
        
        operation_id = f"research_planning_{task_id}_{int(asyncio.get_event_loop().time())}"
        operation = checkpoint_manager.create_operation(operation_id, "Chief_Researcher", research_steps)
        
        await self._execute_tracked_operation(ctx, operation)
        
        domi_state.metadata[planning_executed_key] = True
        print("[Chief_Researcher]: Running LLM agent to synthesize and finalize research planning...")
        async for event in super()._run_async_impl(ctx):
            yield event

    async def _execute_tracked_operation(self, ctx: InvocationContext, operation: TrackedOperation):
        """Executes all steps in a tracked operation."""
        print(f"[Chief_Researcher]: Executing operation '{operation.operation_id}' with {len(operation.get_remaining_steps())} steps.")
        
        with operation as (tracker, steps):
            tasks = [self._run_step(step, ctx, tracker) for step in steps]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            successful_results = [res for res in results if not isinstance(res, Exception)]
            await self._create_planning_summary(ctx, successful_results, operation.operation_id)

    async def _run_step(self, step, ctx, tracker):
        """Executes a single step within a tracked context."""
        with tracker.step_context(step):
            try:
                result = await self._execute_planning_step(ctx, step.input_state)
                print(f"[Chief_Researcher]: ✅ Completed step: {step.step_name}")
                return result
            except Exception as e:
                print(f"[Chief_Researcher]: ❌ Step failed: {step.step_name} - {e}")
                raise
    
    async def _execute_planning_step(self, ctx: InvocationContext, step_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single, real planning step by generating a file."""
        from ..utils.task_loader import load_task_description
        from ..prompts.definitions.chief_researcher_steps import CHIEF_RESEARCHER_STEP_INSTRUCTION
        
        domi_state = get_domi_state(ctx)
        task_id = domi_state.task_id
        task_description = load_task_description(task_id)

        prompt_template = CHIEF_RESEARCHER_STEP_INSTRUCTION.format(
            task_description=task_description,
            step_name=step_config.get('step_name', 'Unknown Step'),
            description=step_config.get('description', 'No description.'),
            filename=os.path.basename(step_config.get('filename', 'unknown.md'))
        )
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
        
        print(f"[Chief_Researcher]:    - Generating content for: {step_name}")
        
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
        print(f"[Chief_Researcher]:    - Writing content to: {filename}")
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
    
    async def _create_planning_summary(self, ctx: InvocationContext, results: List[Dict[str, Any]], operation_id: str):
        """Create a summary of all planning steps."""
        domi_state = get_domi_state(ctx)
        task_id = domi_state.task_id
        outputs_dir = config.get_outputs_dir(task_id)
        
        summary = {
            "domi_task_id": task_id,
            "operation_id": operation_id,
            "total_planning_steps": len(results),
            "successful_steps": len([r for r in results if r.get("status") == "completed"]),
            "failed_steps": len([r for r in results if r.get("status") != "completed"]),
            "planning_details": results,
            "micro_checkpoints_used": True
        }
        
        summary_path = os.path.join(outputs_dir, "planning", f"planning_summary_{operation_id}.json")
        os.makedirs(os.path.dirname(summary_path), exist_ok=True)
        
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        # Update session state
        domi_state.metadata['planning_summary_artifact'] = summary_path
        domi_state.metadata['micro_checkpoints_enabled'] = True
        
        print(f"[Chief_Researcher]: 💾 Planning micro-checkpoint summary created at: {summary_path}")


def get_chief_researcher_agent():
    """Create Chief Researcher agent with micro-checkpoint support."""
    agent_name = "Chief_Researcher"
    
    from ..tools.toolset_registry import toolset_registry
    desktop_commander_toolset = toolset_registry.get_desktop_commander_toolset()
    
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