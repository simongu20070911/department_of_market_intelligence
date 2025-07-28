#!/usr/bin/env python3
"""
MCP Agent Performance Test

This script tests and times each component of the MCP + ADK integration
to identify performance bottlenecks.
"""

import asyncio
import time
import os
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioConnectionParams
from mcp.client.stdio import StdioServerParameters
from google.adk.agents.llm_agent import LlmAgent
from department_of_market_intelligence.utils.model_loader import get_llm_model
from department_of_market_intelligence import config

def time_it(description: str):
    """Decorator to time function execution"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            print(f"\n⏱️  TIMING: {description}")
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                elapsed = time.time() - start_time
                print(f"✅ {description}: {elapsed:.2f} seconds")
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                print(f"❌ {description}: {elapsed:.2f} seconds (FAILED: {e})")
                raise
        return wrapper
    return decorator

@time_it("MCP Desktop Commander Connection")
async def test_mcp_connection():
    """Test MCP connection time"""
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    toolset = MCPToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command=config.DESKTOP_COMMANDER_COMMAND,
                args=config.DESKTOP_COMMANDER_ARGS,
                cwd=project_root
            )
        )
    )
    
    # Initialize and get tools list using correct API
    tools = await toolset.get_tools()
    print(f"   📋 Tools found: {len(tools)} tools")
    
    return toolset

@time_it("LLM Model Initialization")
async def test_llm_init():
    """Test LLM model initialization time"""
    model = get_llm_model("gemini-2.5-pro")
    print(f"   🧠 Model created: {type(model).__name__}")
    return model

@time_it("Simple LLM Call (No Tools)")
async def test_simple_llm_call(model):
    """Test simple LLM call without tools"""
    from google.adk.core.content import Content, ContentPart
    
    request = Content(
        parts=[ContentPart(text="Say 'Hello, I am ready!' and nothing else.")]
    )
    
    async for response in model.generate_content_async(request):
        if response.candidates and response.candidates[0].content:
            content = response.candidates[0].content.parts[0].text
            print(f"   💬 LLM Response: {content[:50]}...")
            return response

@time_it("Agent Creation with Tools")
async def test_agent_creation(model, toolset):
    """Test agent creation with MCP tools"""
    agent = LlmAgent(
        name="Test_Agent",
        llm=model,
        tools=[toolset],
        instructions="You are a test agent. When asked to do something, do it quickly and efficiently."
    )
    print(f"   🤖 Agent created: {agent.name}")
    return agent

@time_it("Tool Schema Generation")
async def test_tool_schema_generation(toolset):
    """Test tool schema generation time"""
    tools = await toolset.get_tools()
    schemas = []
    for tool in tools:
        # Tools should have their schema already available
        schemas.append(tool)
    
    print(f"   📋 Tools retrieved: {len(schemas)} tools")
    return schemas

@time_it("Simple Tool Call (list_directory)")
async def test_simple_tool_call(toolset):
    """Test a simple tool call"""
    # Get tools first to find the list_directory tool
    tools = await toolset.get_tools()
    list_dir_tool = None
    for tool in tools:
        if 'list_directory' in tool.name.lower() or 'list_directory' in str(tool):
            list_dir_tool = tool
            break
    
    if list_dir_tool:
        # Call the tool directly
        from google.adk.core.tool_invocation_context import ToolInvocationContext
        context = ToolInvocationContext(
            invocation_id="test_invocation",
            function_name=list_dir_tool.name,
            arguments={"path": "/home/gaen/agents_gaen"}
        )
        result = await list_dir_tool.call(context)
        print(f"   📂 Tool result: {str(result)[:100]}...")
        return result
    else:
        print(f"   📂 Available tools: {[tool.name for tool in tools[:5]]}...")
        return "Tool not found"

@time_it("Agent with Tool Call")
async def test_agent_tool_call(agent):
    """Test agent making a tool call"""
    from google.adk.core.invocation_context import InvocationContext
    from google.adk.core.content import Content, ContentPart
    
    context = InvocationContext(
        session_id="test_session",
        request=Content(
            parts=[ContentPart(text="List the files in the current directory using the available tools.")]
        )
    )
    
    async for event in agent.run_async(context):
        if hasattr(event, 'content') and event.content:
            print(f"   🎯 Agent response: {str(event.content)[:100]}...")
            return event

async def main():
    """Run all performance tests"""
    print("🚀 Starting MCP Agent Performance Tests")
    print("=" * 60)
    
    try:
        # Test 1: MCP Connection
        toolset = await test_mcp_connection()
        
        # Test 2: LLM Initialization  
        model = await test_llm_init()
        
        # Test 3: Simple LLM Call
        await test_simple_llm_call(model)
        
        # Test 4: Tool Schema Generation
        await test_tool_schema_generation(toolset)
        
        # Test 5: Simple Tool Call
        await test_simple_tool_call(toolset)
        
        # Test 6: Agent Creation
        agent = await test_agent_creation(model, toolset)
        
        # Test 7: Agent Tool Call (This is the slow one!)
        await test_agent_tool_call(agent)
        
        print("\n" + "=" * 60)
        print("🎉 All tests completed!")
        
    except Exception as e:
        print(f"\n💥 Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())