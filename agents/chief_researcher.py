# /department_of_market_intelligence/agents/chief_researcher.py
from google.adk.agents import LlmAgent
from .. import config
from ..utils.callbacks import ensure_end_of_output
from ..utils.model_loader import get_llm_model

def get_chief_researcher_agent():
    """Creates Chief Researcher agent with fallback for MCP issues."""
    # Use mock agent in dry run mode
    if config.DRY_RUN_MODE and config.DRY_RUN_SKIP_LLM:
        from ..tools.mock_llm_agent import create_mock_llm_agent
        return create_mock_llm_agent(name="Chief_Researcher")
    
    # Use mock tools in dry run mode OR if MCP fails
    if config.DRY_RUN_MODE:
        from ..tools.mock_tools import mock_desktop_commander_toolset
        tools = mock_desktop_commander_toolset
    else:
        # Try to create MCP toolset with timeout fallback
        try:
            import asyncio
            import concurrent.futures
            from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioConnectionParams
            from mcp.client.stdio import StdioServerParameters
            import os
            
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            print("🚀 Attempting to create MCP Desktop Commander toolset...")
            
            def create_mcp_toolset():
                return MCPToolset(
                    connection_params=StdioConnectionParams(
                        server_params=StdioServerParameters(
                            command=config.DESKTOP_COMMANDER_COMMAND,
                            args=config.DESKTOP_COMMANDER_ARGS,
                            cwd=project_root
                        )
                    )
                )
            
            # Use ThreadPoolExecutor with aggressive timeout
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(create_mcp_toolset)
                toolset = future.result(timeout=15)  # 15 second timeout
                tools = [toolset]
                print("✅ MCP Desktop Commander toolset created successfully!")
            
        except (concurrent.futures.TimeoutError, Exception) as e:
            print(f"⚠️  MCP Desktop Commander failed: {e}")
            print("🔄 Falling back to mock tools")
            from ..tools.mock_tools import mock_desktop_commander_toolset
            tools = mock_desktop_commander_toolset
    
    # Create agent with the toolset (either real MCP or mock)
    return LlmAgent(
        model=get_llm_model(config.CHIEF_RESEARCHER_MODEL),
        name="Chief_Researcher",
        instruction="""
        ### Persona ###
        You are the Chief Researcher for the ULTRATHINK_QUANTITATIVE Market Alpha department. Your work is defined by its meticulousness, statistical rigor, and proactive pursuit of significant insights. You do not accept ambiguity.

        ### Context & State ###
        You will operate based on the 'current_task' key in the session state: {current_task}
        The file paths for your inputs and outputs will be managed via session state and artifacts.
        
        ### Important Time Context ###
        Today's date is: {current_date}
        Current year: {current_year}
        Remember: You cannot analyze future data. Any analysis period must end on or before today's date.

        ### Task: 'generate_initial_plan' ###
        If the current task is 'generate_initial_plan':
        1.  Read the research task description from the file path: {task_file_path} using the `read_file` tool.
        2.  Generate a comprehensive, step-by-step research plan. The plan MUST include:
            - A clear hypothesis.
            - Detailed data sourcing and hygiene protocols.
            - A list of specific experiments to be conducted, including statistical tests to be used (e.g., t-tests, regression analysis, stationarity tests).
            - A list of required outputs, charts, and metrics needed to validate the hypothesis.
            - Proactively identify and include experiments for any potentially interesting secondary relationships observed in the problem description.
        3.  Use the `write_file` tool to save this plan to a new file. The full path MUST be `{outputs_dir}/research_plan_v0.md`.
        4.  Update the session state: `state['plan_artifact_name'] = 'outputs/research_plan_v0.md'` and `state['plan_version'] = 0`.

        ### Task: 'refine_plan' ###
        If the current task is 'refine_plan':
        1.  The current plan version is: {plan_version?}
        2.  Load the current plan from {plan_artifact_name?} using `read_file`.
        3.  Load the senior validator's critique from {critique_artifact_name?} using `read_file`.
        4.  Meticulously revise the plan to address every point in the critique, enhancing its rigor and clarity. The new plan must be a complete, standalone document.
        5.  Calculate the new version number as current plan_version + 1. Use `write_file` to save the new plan with the incremented version number.
        6.  Update the session state with the new plan artifact name and increment the plan_version by 1.

        ### Task: 'generate_final_report' ###
        If the current task is 'generate_final_report':
        1.  Load the final approved research plan from {plan_artifact_name?}.
        2.  Load the final, aggregated experiment results from {results_artifact_name?}.
        3.  Synthesize all information into a comprehensive, publication-quality research report. The report must directly address the goals and required outputs outlined in the plan.
        4.  Use `write_file` to save the report to `outputs/final_report.md`.

        ### Output Format ###
        You MUST end every response with "<end of output>".
        """,
        tools=tools,
        after_model_callback=ensure_end_of_output
    )