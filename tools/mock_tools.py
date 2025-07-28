# /department_of_market_intelligence/tools/mock_tools.py
"""Mock tools for dry run mode - simulates MCP Desktop Commander functionality."""

from google.adk.tools import FunctionTool
from typing import Dict, Any

async def read_file(path: str) -> str:
    """Mock read_file tool for dry run mode."""
    if "sample_research_task.md" in path:
        return """# Research Task: Analyze Market Microstructure Evolution

## Objective
Conduct a comprehensive analysis of how market microstructure has evolved from 2020-2024, 
focusing on the impact of zero-commission trading, payment for order flow (PFOF), 
and the rise of retail trading platforms.

## Key Areas to Investigate
1. Changes in bid-ask spreads across different asset classes
2. Market depth and liquidity provision mechanisms
3. Impact of gamification on retail trading behavior
4. Regulatory responses and their effectiveness

## Expected Deliverables
- Quantitative analysis with statistical significance testing
- Visualization of key trends
- Policy recommendations based on findings
"""
    return f"[DRY RUN] Mock content from {path}"

async def write_file(path: str, content: str, mode: str) -> str:
    """Mock write_file tool for dry run mode."""
    print(f"[DRY RUN] Would write to {path} ({len(content)} chars)")
    return f"[DRY RUN] Successfully wrote to {path}"

async def create_directory(path: str) -> str:
    """Mock create_directory tool for dry run mode."""
    print(f"[DRY RUN] Would create directory {path}")
    return f"[DRY RUN] Created directory {path}"

async def list_directory(path: str) -> str:
    """Mock list_directory tool for dry run mode."""
    return f"[DRY RUN] Contents of {path}: [mock files]"

async def search_files(path: str, pattern: str) -> str:
    """Mock search_files tool for dry run mode."""
    return f"[DRY RUN] Found 0 files matching '{pattern}' in {path}"

# Create the mock toolset
mock_desktop_commander_toolset = [
    FunctionTool(read_file),
    FunctionTool(write_file),
    FunctionTool(create_directory),
    FunctionTool(list_directory),
    FunctionTool(search_files),
]