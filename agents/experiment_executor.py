# /department_of_market_intelligence/agents/executor.py
import asyncio
import os
import json
from typing import Dict, Any, List, AsyncGenerator
from google.adk.agents import LlmAgent
from google.adk.agents.llm_agent import ReadonlyContext
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from google.genai.types import Content, Part

from .. import config
from ..utils.callbacks import ensure_end_of_output
from ..utils.model_loader import get_llm_model
from ..utils.state_adapter import get_domi_state
from ..utils.checkpoint_manager import CheckpointManager
from ..prompts.definitions.experiment_executor import EXPERIMENT_EXECUTOR_INSTRUCTION


class ExperimentExecutorAgent(LlmAgent):
    """Experiment Executor agent."""
    pass


def get_experiment_executor_agent():
    """Create Experiment Executor agent with micro-checkpoint support."""
    agent_name = "Experiment_Executor"
    
    # Get tools from the registry
    from ..tools.toolset_registry import toolset_registry
    desktop_commander_toolset = toolset_registry.get_desktop_commander_toolset()
    
    tools = [desktop_commander_toolset]
        
    def instruction_provider(ctx: "ReadonlyContext") -> str:
        from ..prompts.builder import inject_template_variables_with_context_preloading
        return inject_template_variables_with_context_preloading(EXPERIMENT_EXECUTOR_INSTRUCTION, ctx, agent_name)
    
    agent = ExperimentExecutorAgent(
        model=get_llm_model(config.AGENT_MODELS["EXECUTOR"]),
        instruction_provider=instruction_provider,
        tools=tools,
        output_key="domi_execution_log_artifact"
    )
    
    from ..utils.micro_checkpoint_wrapper import MicroCheckpointWrapper
    return MicroCheckpointWrapper(agent_factory=lambda: agent, name="Experiment_Executor_Micro_Checkpoint")