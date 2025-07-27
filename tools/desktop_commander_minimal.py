# /department_of_market_intelligence/tools/desktop_commander_minimal.py
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioConnectionParams
from mcp.client.stdio import StdioServerParameters
from .. import config

# This creates a single, reusable toolset with only essential tools
desktop_commander_toolset = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command=config.DESKTOP_COMMANDER_COMMAND,
            args=config.DESKTOP_COMMANDER_ARGS,
        )
    ),
    # Filter to only include essential tools for file operations
    tool_filter=[
        'read_file',
        'write_file',
        'list_directory',
        'create_directory'
    ]
)