# /department_of_market_intelligence/tools/desktop_commander.py
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioConnectionParams
from mcp.client.stdio import StdioServerParameters
from .. import config

# This creates a single, reusable toolset for the Desktop Commander MCP server.
# The ADK framework will manage the lifecycle of the server process.
desktop_commander_toolset = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command=config.DESKTOP_COMMANDER_COMMAND,
            args=config.DESKTOP_COMMANDER_ARGS,
        )
    )
)