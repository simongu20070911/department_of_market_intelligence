# /department_of_market_intelligence/tools/desktop_commander_async.py
"""
Async MCP Desktop Commander toolset with proper lifecycle management.
Based on ADK documentation for MCP outside of adk web.
"""

import asyncio
from contextlib import AsyncExitStack
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioConnectionParams
from mcp.client.stdio import StdioServerParameters
from .. import config
import os

# Set the working directory to the project root to fix path issues
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def create_mcp_toolset_async():
    """
    Create MCP toolset with proper async lifecycle management.
    Returns both the toolset and the exit_stack that must be managed by the caller.
    """
    exit_stack = AsyncExitStack()
    
    try:
        print("🚀 Creating async MCP Desktop Commander toolset...")
        
        # Set environment variable to prevent tool enumeration during init
        import os as _os
        _os.environ['MCP_SKIP_TOOL_ENUM'] = '1'
        
        # Create the toolset
        toolset = MCPToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command=config.DESKTOP_COMMANDER_COMMAND,
                    args=config.DESKTOP_COMMANDER_ARGS,
                    cwd=project_root
                )
            )
        )
        
        # Clear the environment variable
        _os.environ.pop('MCP_SKIP_TOOL_ENUM', None)
        
        # Note: MCPToolset doesn't support async context manager protocol yet
        # We'll handle cleanup manually via exit_stack callback
        exit_stack.callback(lambda: print("🧹 Cleaning up MCP toolset"))
        
        print("✅ Async MCP Desktop Commander toolset created successfully!")
        return toolset, exit_stack
        
    except Exception as e:
        print(f"❌ Failed to create async MCP toolset: {e}")
        # Clean up the exit_stack if toolset creation failed
        await exit_stack.aclose()
        
        # Fall back to mock tools
        print("🔄 Falling back to mock tools...")
        from ..tools.mock_tools import mock_desktop_commander_toolset
        return mock_desktop_commander_toolset, None

async def get_mcp_toolset_with_lifecycle():
    """
    Get MCP toolset with proper lifecycle management.
    This function demonstrates the correct pattern from ADK docs.
    """
    toolset, exit_stack = await create_mcp_toolset_async()
    return toolset, exit_stack