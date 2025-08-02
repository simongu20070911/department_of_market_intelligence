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
                                # Execution mode indicators
                                "DOMI_EXECUTION_MODE": config.EXECUTION_MODE
                            }
                        ),
                        timeout=config.MCP_TIMEOUT_SECONDS
                    )
                )
                
                # Apply high-throughput configuration to ensure 2000/7000 limits
                self._configure_high_throughput_limits()
                
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
    
    def _configure_high_throughput_limits(self):
        """Configure high-throughput limits (2000/7000) for the Desktop Commander instance."""
        try:
            from .tool_config import apply_high_throughput_config
            print("🚀 Configuring high-throughput limits for MCP instance...")
            success = apply_high_throughput_config()
            if success:
                print("✅ High-throughput limits applied to MCP instance")
            else:
                print("⚠️  Failed to apply high-throughput limits")
        except Exception as e:
            print(f"⚠️  Error configuring limits: {e}")
            print("   Desktop Commander will use default limits")
    
    
    def cleanup(self):
        """Clean up MCP resources gracefully."""
        if self._shared_toolset and self._is_real_mcp:
            try:
                # Attempt graceful cleanup
                print("🧹 Cleaning up MCP resources...")
                # Note: MCPToolset doesn't have a standard cleanup method
                # so we'll just clear the reference
                self._shared_toolset = None
                print("✅ MCP cleanup completed")
            except Exception as e:
                # Suppress cleanup errors to avoid masking the original error
                print(f"⚠️  MCP cleanup warning (non-fatal): {e}")
        elif self._shared_toolset:
            print("🧹 Cleaning up mock toolset...")
            self._shared_toolset = None

# Global registry instance
toolset_registry = ToolsetRegistry()