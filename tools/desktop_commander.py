# /department_of_market_intelligence/tools/desktop_commander.py
"""
DEPRECATED: Do not use this module directly.
MCP toolsets should be created inline within agent definitions
to avoid initialization issues during module import.

See ADK documentation on MCP tools for the correct pattern.
"""

# This module is kept for backward compatibility but should not be used.
# All agents should create MCPToolset instances directly in their
# get_*_agent() functions when not in DRY_RUN_MODE.