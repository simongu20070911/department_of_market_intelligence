# /department_of_market_intelligence/agents/coder.py
from google.adk.agents import LlmAgent
from .. import config
from ..utils.callbacks import ensure_end_of_output
from ..utils.model_loader import get_llm_model

def get_coder_agent():
    # Use mock agent in dry run mode
    if config.DRY_RUN_MODE and config.DRY_RUN_SKIP_LLM:
        from ..tools.mock_llm_agent import create_mock_llm_agent
        return create_mock_llm_agent(name="Coder_Agent")
    
    # Get tools from the registry (supports both mock and real MCP)
    from ..tools.toolset_registry import toolset_registry
    desktop_commander_toolset = toolset_registry.get_desktop_commander_toolset()
    
    # Wrap in list if it's a real MCP toolset, mock tools are already a list
    if toolset_registry.is_using_real_mcp():
        tools = [desktop_commander_toolset]
    else:
        tools = desktop_commander_toolset
        
    return LlmAgent(
        model=get_llm_model(config.CODER_MODEL),
        name="Coder_Agent",
        instruction="""
        ### Persona ###
        You are a meticulous and efficient Coder Agent. You write clean, correct, and well-documented Python code to accomplish specific tasks. You follow instructions precisely.

        ### Context & State ###
        - Your specific task is defined in the state dictionary `state['coder_subtask']`. This is a JSON object containing `task_id`, `description`, `dependencies`, `input_artifacts`, `output_artifacts`, and `success_criteria`.
        - If this is a refinement iteration, the critique will be in `state['senior_critique_artifact']`.

        ### Task ###
        1.  Analyze your assigned task from `state['coder_subtask']`.
        2.  If it exists, read the critique from `state['senior_critique_artifact']` to understand required corrections.
        3.  Write the Python code to accomplish the task and meet all success criteria.
        4.  For each artifact you are tasked to create (listed in `output_artifacts`), use the `write_file` tool to save your code. The filename must exactly match the specified output artifact name.

        ### Output Format ###
        You MUST end every response with "<end of output>".
        """,
        tools=tools,
        after_model_callback=ensure_end_of_output
    )