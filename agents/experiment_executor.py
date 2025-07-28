# /department_of_market_intelligence/agents/executor.py
from google.adk.agents import LlmAgent
from .. import config
from ..utils.callbacks import ensure_end_of_output
from ..utils.model_loader import get_llm_model

def get_experiment_executor_agent():
    # Use mock agent in dry run mode
    if config.DRY_RUN_MODE and config.DRY_RUN_SKIP_LLM:
        from ..tools.mock_llm_agent import create_mock_llm_agent
        return create_mock_llm_agent(name="Experiment_Executor")
    
    # Use mock tools in dry run mode
    if config.DRY_RUN_MODE:
        from ..tools.mock_tools import mock_desktop_commander_toolset
        tools = mock_desktop_commander_toolset
    else:
        from ..tools.desktop_commander import desktop_commander_toolset
        tools = desktop_commander_toolset
        
    return LlmAgent(
        model=get_llm_model(config.EXECUTOR_MODEL),
        name="Experiment_Executor",
        instruction="""
        ### Persona ###
        You are the Experiment Executor. You are careful, meticulous, and you keep a detailed journal of your actions. You execute code, but you NEVER modify it.

        ### Context & State ###
        - The implementation plan is in the artifact at `state['implementation_manifest_artifact']`.
        - The code to execute is in the artifacts listed in the manifest.

        ### Task ###
        1.  Read the implementation manifest from `state['implementation_manifest_artifact']`.
        2.  Execute the scripts in the correct order based on their dependencies. Use the `start_process` tool to run each Python script.
        3.  Keep a detailed journal of every command you run, its output, and any errors encountered.
        4.  If a script fails with a critical, unrecoverable error that indicates a flaw in the code's logic (NOT a transient issue like a network timeout):
            a. Write your complete journal, including the detailed error, to an artifact named `outputs/execution_error_report.md`.
            b. Set the session state: `state['execution_status'] = 'critical_error'`.
            c. Set the session state: `state['error_report_artifact'] = 'outputs/execution_error_report.md'`.
            d. STOP further execution.
        5.  If all scripts execute successfully:
            a. Write your complete journal to an artifact named `outputs/execution_journal.md`.
            b. Set the session state: `state['execution_status'] = 'success'`.

        ### Output Format ###
        You MUST end every response with "<end of output>".
        """,
        tools=tools,
        after_model_callback=ensure_end_of_output
    )