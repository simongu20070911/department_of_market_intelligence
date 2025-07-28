# /department_of_market_intelligence/tools/toolset_registry.py
"""
Global toolset registry to manage MCP toolsets with proper lifecycle.
This allows us to inject the real MCP toolset after proper async initialization.
"""

from typing import Optional, Any

class ToolsetRegistry:
    """Registry for managing toolsets with proper lifecycle."""
    
    def __init__(self):
        self._desktop_commander_toolset: Optional[Any] = None
        self._is_real_mcp = False
    
    def set_desktop_commander_toolset(self, toolset: Any, is_real_mcp: bool = False):
        """Set the desktop commander toolset."""
        self._desktop_commander_toolset = toolset
        self._is_real_mcp = is_real_mcp
        print(f"🔧 Toolset registry updated: {'Real MCP' if is_real_mcp else 'Mock'} toolset")
    
    def get_desktop_commander_toolset(self) -> Any:
        """Get the current desktop commander toolset."""
        if self._desktop_commander_toolset is not None:
            return self._desktop_commander_toolset
        
        # Fallback to mock tools (ensure not set as real MCP when falling back)
        self._is_real_mcp = False
        from .mock_tools import mock_desktop_commander_toolset
        return mock_desktop_commander_toolset
    
    def is_using_real_mcp(self) -> bool:
        """Check if we're using real MCP toolset."""
        return self._is_real_mcp

# Global registry instance
toolset_registry = ToolsetRegistry()