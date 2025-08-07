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
    create_data_processing_operation,
    OperationStep
)
from ..utils.micro_checkpoint_manager import micro_checkpoint_manager
from ..prompts.definitions.orchestrator import ORCHESTRATOR_INSTRUCTION


class MicroCheckpointOrchestrator(LlmAgent):
    """Orchestrator with micro-checkpoint support for fine-grained recovery."""
    
    def __init__(self, model, tools, instruction_provider, **kwargs):
        kwargs.setdefault('after_model_callback', ensure_end_of_output)
        super().__init__(
            model=model,
            name="Orchestrator",
            instruction=instruction_provider,
            tools=tools,
            **kwargs
        )
    
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """Enhanced orchestration with fine-grained checkpointing."""
        
        # Check if micro-checkpoints are enabled
        if not config.ENABLE_MICRO_CHECKPOINTS:
            print("🔄 Micro-checkpoints disabled - running standard execution")
            async for event in super()._run_async_impl(ctx):
                yield event
            return
        
        # Use a unique key to track if this pre-orchestration has been done
        task_id = ctx.session.state.get('domi_task_id', config.TASK_ID)
        validation_version = ctx.session.state.get('domi_validation_version', 0)
        orchestration_executed_key = f"orchestrator_planning_executed_v{validation_version}_for_{task_id}"

        if ctx.session.state.get(orchestration_executed_key):
            print("🔄 Micro-checkpoint orchestration already completed for this version. Running LLM agent directly.")
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
        task_id = ctx.session.state.get('domi_task_id', config.TASK_ID)
        outputs_dir = config.get_outputs_dir(task_id)
        
        # Define orchestration steps
        orchestration_steps = [
            {
                "filename": f"{outputs_dir}/planning/parsed_requirements_v{validation_version}.json",
                "name": "Parse Research Plan",
                "description": "Parse the approved research plan and extract key requirements, experiments, and success criteria into a structured JSON format.",
                "expected_outputs": [f"parsed_requirements_v{validation_version}.json"],
                "timeout": 180,
                "max_retries": 2
            },
            {
                "filename": f"{outputs_dir}/planning/implementation_strategy_v{validation_version}.md",
                "name": "Generate Implementation Strategy",
                "description": "Create a detailed implementation strategy document that outlines how the research plan will be translated into parallelizable coding tasks.",
                "expected_outputs": [f"implementation_strategy_v{validation_version}.md"],
                "timeout": 240,
                "max_retries": 2
            },
            {
                "filename": f"{outputs_dir}/planning/execution_graph_v{validation_version}.json",
                "name": "Create Execution Graph",
                "description": "Generate a JSON representation of the task dependency graph for parallel execution, defining dependencies between coding tasks.",
                "expected_outputs": [f"execution_graph_v{validation_version}.json"],
                "timeout": 200,
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
            
            # Mark orchestration as complete before calling the LLM
            ctx.session.state[orchestration_executed_key] = True
            
            # Run standard LLM agent to synthesize and finalize the implementation manifest
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

        # After resuming, run the final synthesis step
        print("🤖 Running LLM agent to synthesize and finalize resumed orchestration...")
        async for event in super()._run_async_impl(ctx):
            yield event
    
    async def _execute_orchestration_step(self, ctx: InvocationContext, step_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single, real orchestration step by generating a file."""
        plan_path = ctx.session.state.get('domi_plan_artifact_name')
        if not plan_path or not os.path.exists(plan_path):
            raise FileNotFoundError("Approved research plan artifact not found in session state.")
        
        with open(plan_path, 'r') as f:
            research_plan_content = f.read()

        prompt_template = f"""
        You are the Orchestrator. You have been given the following approved research plan:
        ---
        {research_plan_content}
        ---
        You are now performing one specific sub-step of the implementation planning phase.
        
        Sub-step Name: {step_config['name']}
        Sub-step Goal: {step_config['description']}
        
        Generate the complete and detailed content for the document: `{os.path.basename(step_config['filename'])}`.
        Your response must ONLY be the raw content for this file (e.g., JSON or Markdown). Do not include any other commentary.
        """
        # Use the generic helper to execute the step
        return await self._execute_step_with_llm(ctx, step_config, prompt_template)

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

    async def _execute_step_with_llm(self, ctx: InvocationContext, step_config: Dict[str, Any], prompt: str) -> Dict[str, Any]:
        """Generic helper to execute a step that generates a file via LLM."""
        # --- FIX: Import necessary ADK/GenAI types ---
        from google.genai.types import Content, Part
        
        step_name = step_config.get("name", "Unknown_Step")
        filename = step_config.get("filename", step_config.get("expected_outputs", ["unknown.out"])[0])
        
        print(f"   🧠 Generating content for: {step_name}")
        
        # --- FIX: Replace the incorrect `acompletion` call with the standard ADK method ---
        request_content = Content(parts=[Part(text=prompt)])
        content_to_write = ""
        
        # The generate_content_async method returns a stream of LlmResponse objects
        # This is the correct, standard way to interact with the model in ADK.
        async for llm_response in self.model.generate_content_async(request_content):
            if llm_response.text:
                content_to_write += llm_response.text
        
        content_to_write = content_to_write.strip()
        # --- END FIX ---

        # Clean up code blocks if the model wraps the output
        if content_to_write.startswith("```"):
            content_to_write = content_to_write.split('\n', 1)[1]
            if content_to_write.endswith("```"):
                content_to_write = content_to_write[:-3].strip()

        print(f"   ✍️ Writing content to: {filename}")
        write_tool = self._find_tool("write_file")
        
        # The tool call logic is correct, just needs the corrected content.
        tool_event_generator = write_tool.run_async(
            args={'path': filename, 'content': content_to_write},
            tool_context=None
        )
        
        # Consume the generator to ensure the tool call completes
        async for _ in tool_event_generator:
            pass

        return {
            "step_name": step_name,
            "description": step_config.get("description", ""),
            "status": "completed",
            "method": "micro_checkpoint_execution",
            "expected_outputs": step_config.get("expected_outputs", []),
            "config": step_config
        }
    
    async def _create_orchestration_summary(self, ctx: InvocationContext, results: List[Dict[str, Any]]):
        """Create a summary of all orchestration steps."""
        task_id = ctx.session.state.get('domi_task_id', config.TASK_ID)
        outputs_dir = config.get_outputs_dir(task_id)
        
        summary = {
            "domi_task_id": task_id,
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
        ctx.session.state['domi_orchestration_summary_artifact'] = summary_path
        ctx.session.state['domi_micro_checkpoints_enabled'] = True
        
        print(f"💾 Orchestration micro-checkpoint summary: {summary_path}")


def get_orchestrator_agent():
    """Create Orchestrator agent with micro-checkpoint support."""
    agent_name = "Orchestrator"
    
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
        return inject_template_variables_with_context_preloading(ORCHESTRATOR_INSTRUCTION, ctx, agent_name)
    
    agent = MicroCheckpointOrchestrator(
        model=get_llm_model(config.ORCHESTRATOR_MODEL),
        instruction_provider=instruction_provider,
        tools=tools,
        output_key="domi_implementation_manifest_artifact"
    )
    
    return agent