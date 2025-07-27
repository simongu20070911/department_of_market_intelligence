# /department_of_market_intelligence/tools/desktop_commander_simple.py
from google.adk.tools import FunctionTool
from typing import Dict, Any

async def list_files_tool(path: str) -> str:
    """List files in a directory (placeholder for testing)"""
    return f"[Placeholder] Files in {path}: file1.txt, file2.md, file3.py"

async def read_file_tool(path: str) -> str:
    """Read a file (placeholder for testing)"""
    return f"[Placeholder] Content of {path}: This is placeholder content."

async def write_file_tool(path: str, content: str) -> str:
    """Write content to a file (placeholder for testing)"""
    return f"[Placeholder] Wrote {len(content)} characters to {path}"

# Create simple placeholder tools for testing
simple_desktop_commander_toolset = [
    FunctionTool(list_files_tool),
    FunctionTool(read_file_tool),
    FunctionTool(write_file_tool),
]