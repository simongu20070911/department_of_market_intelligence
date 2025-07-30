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
    
    # Create tools based on execution mode
    from ..utils.tool_factory import create_agent_tools
    tools = create_agent_tools("Chief_Researcher")
    
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