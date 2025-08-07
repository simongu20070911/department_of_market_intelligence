# /department_of_market_intelligence/tools/toolset_registry.py
"""
Global toolset registry that shares a single MCP connection.
This prevents async task conflicts when multiple agents need tools.
"""

from typing import Optional, Any, List
from .. import config
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ToolsetRegistry:
    """Registry that maintains a single shared MCP connection."""
    
    def __init__(self):
        self._shared_toolset: Optional[Any] = None
    
    def get_desktop_commander_toolset(self) -> Any:
        """Get shared toolset to prevent MCP connection conflicts."""
        if self._shared_toolset is None:
            raise RuntimeError("Toolset not initialized. Call set_desktop_commander_toolset first.")
        return self._shared_toolset
    
    def set_desktop_commander_toolset(self, toolset: Any):
        """Set the shared toolset (used by main.py initialization)."""
        if self._shared_toolset is not None:
            logger.warning("⚠️ Toolset is being re-initialized.")
        self._shared_toolset = toolset
        self._configure_high_throughput_limits()
        logger.info("🔧 Shared MCP toolset has been set.")
    
    def _configure_high_throughput_limits(self):
        """Configure high-throughput limits (2000/7000) for the Desktop Commander instance."""
        try:
            from .tool_config import apply_high_throughput_config
            logger.info("🚀 Configuring high-throughput limits for MCP instance...")
            success = apply_high_throughput_config()
            if success:
                logger.info("✅ High-throughput limits applied to MCP instance")
            else:
                logger.warning("⚠️  Failed to apply high-throughput limits")
        except Exception as e:
            logger.error(f"⚠️  Error configuring limits: {e}")
            logger.warning("   Desktop Commander will use default limits")
    
    

# Global registry instance
toolset_registry = ToolsetRegistry()