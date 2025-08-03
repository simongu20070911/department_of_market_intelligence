# /department_of_market_intelligence/agents/agent_factory.py
"""
Async agent factory to support proper MCP lifecycle management.
Agents are created asynchronously after MCP toolset initialization.
"""

from typing import Dict, Callable, Any
from google.adk.agents import LlmAgent, BaseAgent
from .. import config
from ..utils.callbacks import ensure_end_of_output
from ..utils.model_loader import get_llm_model
from ..tools.toolset_registry import toolset_registry
from ..prompts.builder import inject_template_variables_with_context_preloading
from .chief_researcher import MicroCheckpointChiefResearcher, CHIEF_RESEARCHER_INSTRUCTION
from .orchestrator import MicroCheckpointOrchestrator, ORCHESTRATOR_INSTRUCTION

# Cache for created agents
_agent_cache: Dict[str, BaseAgent] = {}

async def get_chief_researcher_agent_async() -> LlmAgent:
    """Get or create Chief Researcher agent asynchronously."""
    agent_name = "Chief_Researcher"
    if agent_name in _agent_cache:
        return _agent_cache[agent_name]
    
    # Only use mock agent in actual dry_run mode with LLM skipping
    if config.EXECUTION_MODE == "dry_run" and config.DRY_RUN_SKIP_LLM:
        from ..tools.mock_llm_agent import create_mock_llm_agent
        agent = create_mock_llm_agent(name=agent_name)
        _agent_cache[agent_name] = agent
        return agent
    
    # Get tools from the registry
    desktop_commander_toolset = toolset_registry.get_desktop_commander_toolset()
    
    # Wrap in list if it's a real MCP toolset, mock tools are already a list
    tools = [desktop_commander_toolset] if toolset_registry.is_using_real_mcp() else desktop_commander_toolset
    
    def instruction_provider(ctx=None) -> str:
        return inject_template_variables_with_context_preloading(CHIEF_RESEARCHER_INSTRUCTION, ctx, agent_name)
    
    agent = MicroCheckpointChiefResearcher(
        model=get_llm_model(config.CHIEF_RESEARCHER_MODEL),
        instruction_provider=instruction_provider,
        tools=tools,
        after_model_callback=ensure_end_of_output,
        output_key="plan_artifact_name"
    )
    
    _agent_cache[agent_name] = agent
    return agent

async def get_orchestrator_agent_async() -> LlmAgent:
    """Get or create Orchestrator agent asynchronously."""
    agent_name = "Orchestrator"
    if agent_name in _agent_cache:
        return _agent_cache[agent_name]
    
    # Only use mock agent in actual dry_run mode with LLM skipping
    if config.EXECUTION_MODE == "dry_run" and config.DRY_RUN_SKIP_LLM:
        from ..tools.mock_llm_agent import create_mock_llm_agent
        agent = create_mock_llm_agent(name=agent_name)
        _agent_cache[agent_name] = agent
        return agent
    
    # Get tools from the registry
    desktop_commander_toolset = toolset_registry.get_desktop_commander_toolset()
    
    # Wrap in list if it's a real MCP toolset, mock tools are already a list
    tools = [desktop_commander_toolset] if toolset_registry.is_using_real_mcp() else desktop_commander_toolset
        
    def instruction_provider(ctx=None) -> str:
        return inject_template_variables_with_context_preloading(ORCHESTRATOR_INSTRUCTION, ctx, agent_name)
    
    agent = MicroCheckpointOrchestrator(
        model=get_llm_model(config.ORCHESTRATOR_MODEL),
        instruction_provider=instruction_provider,
        tools=tools,
        output_key="implementation_manifest_artifact"
    )
    
    _agent_cache[agent_name] = agent
    return agent

# Add similar async functions for other agents...
# For now, let's create a generic fallback that uses the existing synchronous functions

def clear_agent_cache():
    """Clear the agent cache (useful for testing)."""
    _agent_cache.clear()