#!/usr/bin/env python3
"""Test script to validate comprehensive dry run path testing functionality."""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from tools.mock_tools import (
    read_file, write_file, create_directory, 
    get_dry_run_summary, reset_dry_run_state
)
import config

async def test_path_validation():
    """Test the enhanced dry run path validation system."""
    print("🧪 TESTING COMPREHENSIVE DRY RUN PATH VALIDATION")
    print("=" * 60)
    
    # Reset state for clean testing
    reset_dry_run_state()
    
    print(f"✅ Task ID: {config.TASK_ID}")
    print(f"✅ Expected path pattern: outputs/{config.TASK_ID}/")
    print()
    
    # Test 1: Correct path usage
    print("🧪 Test 1: Correct task-specific paths")
    correct_path = f"/home/gaen/agents_gaen/department_of_market_intelligence/outputs/{config.TASK_ID}/research_plan_v0.md"
    await write_file(correct_path, "Test research plan content", "rewrite")
    content = await read_file(correct_path)
    print(f"✅ Read back: {len(content)} chars")
    print()
    
    # Test 2: Incorrect path usage (should trigger warnings)
    print("🧪 Test 2: Incorrect old task paths (should warn)")
    wrong_path = "/home/gaen/agents_gaen/department_of_market_intelligence/outputs/default_research_task/research_plan_v1.md"
    await write_file(wrong_path, "This should trigger path inconsistency warning", "rewrite")
    print()
    
    # Test 3: Non-task files (should be OK)
    print("🧪 Test 3: Non-task files (should be OK)")
    task_file_path = "/home/gaen/agents_gaen/department_of_market_intelligence/tasks/sample_research_task.md"
    task_content = await read_file(task_file_path)
    print(f"✅ Task file read: {len(task_content)} chars")
    print()
    
    # Test 4: Directory operations
    print("🧪 Test 4: Directory operations")
    correct_dir = f"/home/gaen/agents_gaen/department_of_market_intelligence/outputs/{config.TASK_ID}"
    await create_directory(correct_dir)
    print()
    
    # Test 5: Critique files
    print("🧪 Test 5: Critique file operations")
    critique_path = f"/home/gaen/agents_gaen/department_of_market_intelligence/outputs/{config.TASK_ID}/critique_junior_v0.md"
    await write_file(critique_path, "Mock critique content", "rewrite")
    critique_content = await read_file(critique_path)
    print(f"✅ Critique read: {len(critique_content)} chars")
    print()
    
    # Generate comprehensive summary
    print("📋 FINAL VALIDATION SUMMARY:")
    print("=" * 60)
    summary = get_dry_run_summary()
    print(summary)
    
    return summary

if __name__ == "__main__":
    asyncio.run(test_path_validation())