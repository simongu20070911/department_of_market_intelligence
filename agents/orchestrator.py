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
from ..utils.state_adapter import get_domi_state
from ..utils.operation_tracking import (
    create_data_processing_operation,
    OperationStep
)
from ..prompts.definitions.orchestrator import ORCHESTRATOR_INSTRUCTION
from ..utils.logger import get_logger

logger = get_logger(__name__)


class OrchestratorAgent(LlmAgent):
    """Orchestrates the implementation of the research plan."""
    
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
        """Executes the orchestration logic."""
        domi_state = get_domi_state(ctx)
        logger.info(f"[Orchestrator]: Executing task: {domi_state.current_task_description}")
        async for event in super()._run_async_impl(ctx):
            yield event

def get_orchestrator_agent():
    """Creates and returns the Orchestrator agent."""
    agent_name = "Orchestrator"
    
    from ..tools.toolset_registry import toolset_registry
    desktop_commander_toolset = toolset_registry.get_desktop_commander_toolset()
    
    tools = [desktop_commander_toolset]
        
    def instruction_provider(ctx: "ReadonlyContext") -> str:
        from ..prompts.builder import inject_template_variables_with_context_preloading
        return inject_template_variables_with_context_preloading(ORCHESTRATOR_INSTRUCTION, ctx, agent_name)
    
    agent = OrchestratorAgent(
        model=get_llm_model(config.AGENT_MODELS["ORCHESTRATOR"]),
        instruction_provider=instruction_provider,
        tools=tools,
        output_key="domi_implementation_manifest_artifact"
    )
    
    from ..utils.micro_checkpoint_wrapper import MicroCheckpointWrapper
    return MicroCheckpointWrapper(agent_factory=lambda: agent, name="Orchestrator_Micro_Checkpoint")