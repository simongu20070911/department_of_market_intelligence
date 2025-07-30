# /department_of_market_intelligence/agents/orchestrator.py
from google.adk.agents import LlmAgent
from google.adk.agents.llm_agent import ReadonlyContext
from .. import config
from ..utils.callbacks import ensure_end_of_output
from ..utils.model_loader import get_llm_model
from ..prompts.definitions.orchestrator import ORCHESTRATOR_INSTRUCTION

def get_orchestrator_agent():
    # Only use mock agent in actual dry_run mode with LLM skipping
    if config.EXECUTION_MODE == "dry_run" and config.DRY_RUN_SKIP_LLM:
        from ..tools.mock_llm_agent import create_mock_llm_agent
        return create_mock_llm_agent(name="Orchestrator")
    
    # Create tools based on execution mode
    from ..utils.tool_factory import create_agent_tools
    tools = create_agent_tools("Orchestrator")
        
    # Create instruction provider for dynamic template variable injection
    def instruction_provider(ctx: ReadonlyContext) -> str:
        from ..prompts.builder import inject_template_variables
        return inject_template_variables(ORCHESTRATOR_INSTRUCTION, ctx, "Orchestrator")
    
    return LlmAgent(
        model=get_llm_model(config.ORCHESTRATOR_MODEL),
        name="Orchestrator",
        instruction=instruction_provider,
        tools=tools,
        after_model_callback=ensure_end_of_output
    )