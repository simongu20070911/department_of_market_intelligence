# /department_of_market_intelligence/agents/orchestrator.py
from google.adk.agents import LlmAgent
from .. import config
from ..utils.callbacks import ensure_end_of_output
from ..utils.model_loader import get_llm_model
from ..prompts.definitions.orchestrator import ORCHESTRATOR_INSTRUCTION

def get_orchestrator_agent():
    # Use mock agent in dry run mode
    if config.DRY_RUN_MODE and config.DRY_RUN_SKIP_LLM:
        from ..tools.mock_llm_agent import create_mock_llm_agent
        return create_mock_llm_agent(name="Orchestrator")
    
    # Use mock tools in dry run mode
    if config.DRY_RUN_MODE:
        from ..tools.mock_tools import mock_desktop_commander_toolset
        tools = mock_desktop_commander_toolset
    else:
        # Create MCP toolset inline as per ADK documentation
        from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioConnectionParams
        from mcp.client.stdio import StdioServerParameters
        import os
        
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        tools = [
            MCPToolset(
                connection_params=StdioConnectionParams(
                    server_params=StdioServerParameters(
                        command=config.DESKTOP_COMMANDER_COMMAND,
                        args=config.DESKTOP_COMMANDER_ARGS,
                        cwd=project_root
                    )
                )
            )
        ]
        
    return LlmAgent(
        model=get_llm_model(config.ORCHESTRATOR_MODEL),
        name="Orchestrator",
        instruction=ORCHESTRATOR_INSTRUCTION,
        tools=tools,
        after_model_callback=ensure_end_of_output
    )