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

# Cache for created agents
_agent_cache: Dict[str, BaseAgent] = {}

async def get_chief_researcher_agent_async() -> LlmAgent:
    """Get or create Chief Researcher agent asynchronously."""
    if "Chief_Researcher" in _agent_cache:
        return _agent_cache["Chief_Researcher"]
    
    # Only use mock agent in actual dry_run mode with LLM skipping
    if config.EXECUTION_MODE == "dry_run" and config.DRY_RUN_SKIP_LLM:
        from ..tools.mock_llm_agent import create_mock_llm_agent
        agent = create_mock_llm_agent(name="Chief_Researcher")
        _agent_cache["Chief_Researcher"] = agent
        return agent
    
    # Get tools from the registry
    desktop_commander_toolset = toolset_registry.get_desktop_commander_toolset()
    
    # Wrap in list if it's a real MCP toolset, mock tools are already a list
    if toolset_registry.is_using_real_mcp():
        tools = [desktop_commander_toolset]
    else:
        tools = desktop_commander_toolset
    
    # Import instruction here to avoid circular imports
    from .chief_researcher import CHIEF_RESEARCHER_INSTRUCTION
    
    agent = LlmAgent(
        model=get_llm_model(config.CHIEF_RESEARCHER_MODEL),
        name="Chief_Researcher",
        instruction=CHIEF_RESEARCHER_INSTRUCTION,
        tools=tools,
        after_model_callback=ensure_end_of_output,
        output_key="research_plan_path"
    )
    
    _agent_cache["Chief_Researcher"] = agent
    return agent

async def get_orchestrator_agent_async() -> LlmAgent:
    """Get or create Orchestrator agent asynchronously."""
    if "Orchestrator" in _agent_cache:
        return _agent_cache["Orchestrator"]
    
    # Only use mock agent in actual dry_run mode with LLM skipping
    if config.EXECUTION_MODE == "dry_run" and config.DRY_RUN_SKIP_LLM:
        from ..tools.mock_llm_agent import create_mock_llm_agent
        agent = create_mock_llm_agent(name="Orchestrator")
        _agent_cache["Orchestrator"] = agent
        return agent
    
    # Get tools from the registry
    desktop_commander_toolset = toolset_registry.get_desktop_commander_toolset()
    
    # Wrap in list if it's a real MCP toolset, mock tools are already a list
    if toolset_registry.is_using_real_mcp():
        tools = [desktop_commander_toolset]
    else:
        tools = desktop_commander_toolset
        
    # Import instruction here to avoid circular imports
    from .orchestrator import ORCHESTRATOR_INSTRUCTION
    
    agent = LlmAgent(
        model=get_llm_model(config.ORCHESTRATOR_MODEL),
        name="Orchestrator",
        instruction=ORCHESTRATOR_INSTRUCTION,
        tools=tools,
        after_model_callback=ensure_end_of_output,
        output_key="implementation_manifest_path"
    )
    
    _agent_cache["Orchestrator"] = agent
    return agent

# Add similar async functions for other agents...
# For now, let's create a generic fallback that uses the existing synchronous functions

def clear_agent_cache():
    """Clear the agent cache (useful for testing)."""
    _agent_cache.clear()