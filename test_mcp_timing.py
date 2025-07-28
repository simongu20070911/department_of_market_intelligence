#!/usr/bin/env python3
"""
Simplified MCP Timing Test

Focus on the agent tool call timing issue.
"""

import asyncio
import time
import os
import sys

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

@time_it("Agent Tool Call (The Slow One)")
async def test_agent_tool_call(agent):
    """Test agent making a tool call - this is what takes ~1 minute"""
    from google.adk.core.invocation_context import InvocationContext
    from google.adk.core.message import Message, MessageRole
    
    context = InvocationContext(
        session_id="test_session",
        request=Message(
            role=MessageRole.USER,
            content="List the files in the current directory using the available tools."
        )
    )
    
    async for event in agent.run_async(context):
        if hasattr(event, 'content') and event.content:
            print(f"   🎯 Agent response: {str(event.content)[:100]}...")
            return event

async def main():
    """Run focused performance tests"""
    print("🚀 Starting Focused MCP Timing Tests")
    print("=" * 60)
    
    try:
        # Test 1: MCP Connection (takes ~1.4 seconds)
        print("Testing MCP connection...")
        toolset = await test_mcp_connection()
        
        # Test 2: LLM Model (fast)
        print("Creating LLM model...")
        model = get_llm_model("gemini-2.5-pro")
        print(f"   🧠 Model created: {type(model).__name__}")
        
        # Test 3: Agent Creation (should be fast)
        print("Creating agent with tools...")
        agent = await test_agent_creation(model, toolset)
        
        # Test 4: Agent Tool Call (This is the suspected slow one!)
        print("Testing agent tool call - this might take ~1 minute...")
        await test_agent_tool_call(agent)
        
        print("\n" + "=" * 60)
        print("🎉 Timing tests completed!")
        
    except Exception as e:
        print(f"\n💥 Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())