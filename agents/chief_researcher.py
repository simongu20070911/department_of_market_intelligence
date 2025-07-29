# /department_of_market_intelligence/agents/chief_researcher.py
from google.adk.agents import LlmAgent
from .. import config
from ..utils.model_loader import get_llm_model
from ..prompts.definitions.chief_researcher import CHIEF_RESEARCHER_INSTRUCTION

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
                        ),
                        timeout=config.MCP_TIMEOUT_SECONDS  # Use config timeout instead of default 5.0
                    )
                )
            
            # Use ThreadPoolExecutor with extended timeout
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(create_mcp_toolset)
                toolset = future.result(timeout=config.MCP_TIMEOUT_SECONDS + 10)  # MCP timeout + buffer
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
        instruction=CHIEF_RESEARCHER_INSTRUCTION,
        tools=tools
    )