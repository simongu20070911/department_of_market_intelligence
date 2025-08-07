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
from ..utils.checkpoint_manager import CheckpointManager
from ..prompts.definitions.chief_researcher import CHIEF_RESEARCHER_INSTRUCTION


class ChiefResearcherAgent(LlmAgent):
    """Chief Researcher agent."""
    pass


def get_chief_researcher_agent():
    """Create Chief Researcher agent with micro-checkpoint support."""
    agent_name = "Chief_Researcher"
    
    from ..tools.toolset_registry import toolset_registry
    desktop_commander_toolset = toolset_registry.get_desktop_commander_toolset()
    
    tools = [desktop_commander_toolset]
    
    def instruction_provider(ctx=None) -> str:
        from ..prompts.builder import inject_template_variables_with_context_preloading
        return inject_template_variables_with_context_preloading(CHIEF_RESEARCHER_INSTRUCTION, ctx, agent_name)
    
    agent = ChiefResearcherAgent(
        model=get_llm_model(config.AGENT_MODELS["CHIEF_RESEARCHER"]),
        name="Chief_Researcher",
        instruction=instruction_provider,
        tools=tools,
        after_model_callback=ensure_end_of_output,
        output_key="plan_artifact_name"
    )
    
    from ..utils.micro_checkpoint_wrapper import MicroCheckpointWrapper
    return MicroCheckpointWrapper(agent_factory=lambda: agent, name="Chief_Researcher_Micro_Checkpoint")