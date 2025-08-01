# /department_of_market_intelligence/agents/chief_researcher.py
from google.adk.agents import LlmAgent
from google.adk.agents.llm_agent import ReadonlyContext
from .. import config
from ..utils.model_loader import get_llm_model
from ..prompts.definitions.chief_researcher import CHIEF_RESEARCHER_INSTRUCTION

def get_chief_researcher_agent():
    """Creates Chief Researcher agent with execution-mode-aware tools."""
    # Only use mock agent in actual dry_run mode with LLM skipping
    if config.EXECUTION_MODE == "dry_run" and config.DRY_RUN_SKIP_LLM:
        from ..tools.mock_llm_agent import create_mock_llm_agent
        return create_mock_llm_agent(name="Chief_Researcher")
    
    # Use the centralized toolset registry
    from ..tools.toolset_registry import toolset_registry
    desktop_commander_toolset = toolset_registry.get_desktop_commander_toolset()
    
    # Wrap in list if it's a real MCP toolset, mock tools are already a list
    if toolset_registry.is_using_real_mcp():
        tools = [desktop_commander_toolset]
    else:
        tools = desktop_commander_toolset
    
    # Create instruction provider for dynamic template variable injection
    def instruction_provider(ctx: "ReadonlyContext") -> str:
        from ..prompts.builder import inject_template_variables
        return inject_template_variables(CHIEF_RESEARCHER_INSTRUCTION, ctx, "Chief_Researcher")
    
    # Create agent with the toolset (either real MCP or mock)
    return LlmAgent(
        model=get_llm_model(config.CHIEF_RESEARCHER_MODEL),
        name="Chief_Researcher",
        instruction=instruction_provider,
        tools=tools
    )