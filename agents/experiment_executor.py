# /department_of_market_intelligence/agents/executor.py
from google.adk.agents import LlmAgent
from google.adk.agents.llm_agent import ReadonlyContext
from .. import config
from ..utils.callbacks import ensure_end_of_output
from ..utils.model_loader import get_llm_model
from ..prompts.definitions.experiment_executor import EXPERIMENT_EXECUTOR_INSTRUCTION

def get_experiment_executor_agent():
    """Create Experiment Executor agent with execution-mode-aware tools."""
    # Only use mock agent in actual dry_run mode with LLM skipping
    if config.EXECUTION_MODE == "dry_run" and config.DRY_RUN_SKIP_LLM:
        from ..tools.mock_llm_agent import create_mock_llm_agent
        return create_mock_llm_agent(name="Experiment_Executor")
    
    # Create tools based on execution mode
    from ..utils.tool_factory import create_agent_tools
    tools = create_agent_tools("Experiment_Executor")
    
    # Create instruction provider for dynamic template variable injection
    def instruction_provider(ctx: "ReadonlyContext") -> str:
        from ..prompts.builder import inject_template_variables
        return inject_template_variables(EXPERIMENT_EXECUTOR_INSTRUCTION, ctx, "Experiment_Executor")
        
    return LlmAgent(
        model=get_llm_model(config.EXECUTOR_MODEL),
        name="Experiment_Executor",
        instruction=instruction_provider,
        tools=tools,
        after_model_callback=ensure_end_of_output
    )