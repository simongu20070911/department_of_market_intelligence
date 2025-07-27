# /department_of_market_intelligence/tools/simple_file_tools.py
# Simple file tools as a temporary alternative to MCP
from google.adk.tools import FunctionTool
import os
import json
from typing import List, Dict, Any

async def read_file(path: str) -> str:
    """Read the contents of a file"""
    try:
        with open(path, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

async def write_file(path: str, content: str) -> str:
    """Write content to a file"""
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            f.write(content)
        return f"Successfully wrote {len(content)} characters to {path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

async def list_directory(path: str) -> str:
    """List files in a directory"""
    try:
        files = os.listdir(path)
        return json.dumps({"files": files}, indent=2)
    except Exception as e:
        return f"Error listing directory: {str(e)}"

async def create_directory(path: str) -> str:
    """Create a directory"""
    try:
        os.makedirs(path, exist_ok=True)
        return f"Successfully created directory: {path}"
    except Exception as e:
        return f"Error creating directory: {str(e)}"

# Create toolset
simple_file_toolset = [
    FunctionTool(read_file),
    FunctionTool(write_file),
    FunctionTool(list_directory),
    FunctionTool(create_directory),
]