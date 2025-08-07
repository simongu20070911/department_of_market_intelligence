# /department_of_market_intelligence/agents/coder.py
from google.adk.agents import LlmAgent
from google.adk.agents.llm_agent import ReadonlyContext
from .. import config
from ..utils.callbacks import ensure_end_of_output
from ..utils.model_loader import get_llm_model
from ..utils.state_adapter import get_domi_state
from ..prompts.definitions.coder import CODER_INSTRUCTION
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from typing import AsyncGenerator

class CoderAgent(LlmAgent):
    """Coder agent."""
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """Executes the coding logic."""
        domi_state = get_domi_state(ctx)
        print(f"[Coder_Agent]: Executing task: {domi_state.current_task_description}")
        async for event in super()._run_async_impl(ctx):
            yield event

def get_coder_agent():
    """Create Coder agent with execution-mode-aware tools."""
    from ..tools.toolset_registry import toolset_registry
    desktop_commander_toolset = toolset_registry.get_desktop_commander_toolset()
    tools = [desktop_commander_toolset]
    
    # Create instruction provider for dynamic template variable injection with context pre-loading
    def instruction_provider(ctx: "ReadonlyContext") -> str:
        from ..prompts.builder import inject_template_variables_with_context_preloading
        return inject_template_variables_with_context_preloading(CODER_INSTRUCTION, ctx, "Coder_Agent")
        
    agent = CoderAgent(
        model=get_llm_model(config.AGENT_MODELS["CODER"]),
        name="Coder_Agent",
        instruction=instruction_provider,
        tools=tools,
        after_model_callback=ensure_end_of_output
    )

    from ..utils.micro_checkpoint_wrapper import MicroCheckpointWrapper
    return MicroCheckpointWrapper(agent_factory=lambda: agent, name="Coder_Agent_Micro_Checkpoint")