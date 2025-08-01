# /department_of_market_intelligence/tools/toolset_registry.py
"""
Global toolset registry that shares a single MCP connection.
This prevents async task conflicts when multiple agents need tools.
"""

from typing import Optional, Any, List
from .. import config

class ToolsetRegistry:
    """Registry that maintains a single shared MCP connection."""
    
    def __init__(self):
        self._shared_toolset: Optional[Any] = None
        self._is_real_mcp = False
        self._mode = config.EXECUTION_MODE
    
    def get_desktop_commander_toolset(self) -> Any:
        """Get shared toolset to prevent MCP connection conflicts."""
        if self._shared_toolset is not None:
            return self._shared_toolset
        
        # Create the shared toolset once
        if config.EXECUTION_MODE == "dry_run":
            from .mock_tools import mock_desktop_commander_toolset
            self._shared_toolset = mock_desktop_commander_toolset
            self._is_real_mcp = False
        else:
            # Create single MCP toolset with proper configuration
            try:
                from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioConnectionParams
                from mcp.client.stdio import StdioServerParameters
                import os
                
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                
                self._shared_toolset = MCPToolset(
                    connection_params=StdioConnectionParams(
                        server_params=StdioServerParameters(
                            command=config.DESKTOP_COMMANDER_COMMAND,
                            args=config.DESKTOP_COMMANDER_ARGS,
                            cwd=project_root,
                            env={
                                **os.environ,
                                # Configure Desktop Commander limits for larger files
                                "DC_FILE_WRITE_LINE_LIMIT": "10000",
                                "DC_FILE_READ_LINE_LIMIT": "15000",
                                # Execution mode indicators
                                "DOMI_EXECUTION_MODE": config.EXECUTION_MODE
                            }
                        ),
                        timeout=config.MCP_TIMEOUT_SECONDS
                    )
                )
                self._is_real_mcp = True
                print(f"🔧 Shared MCP toolset created for {config.EXECUTION_MODE} mode")
                
            except Exception as e:
                print(f"❌ Failed to create MCP toolset: {e}")
                print("🔄 Falling back to mock tools")
                from .mock_tools import mock_desktop_commander_toolset
                self._shared_toolset = mock_desktop_commander_toolset
                self._is_real_mcp = False
        
        return self._shared_toolset
    
    def set_desktop_commander_toolset(self, toolset: Any, is_real_mcp: bool = False):
        """Set the shared toolset (used by main.py initialization)."""
        self._shared_toolset = toolset
        self._is_real_mcp = is_real_mcp
        print(f"🔧 Toolset registry: {'Real MCP' if is_real_mcp else 'Mock'} toolset set")
    
    def is_using_real_mcp(self) -> bool:
        """Check if we're using real MCP toolset."""
        return self._is_real_mcp

# Global registry instance
toolset_registry = ToolsetRegistry()