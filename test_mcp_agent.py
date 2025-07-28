#!/usr/bin/env python3
"""
Test agent to verify MCP Desktop Commander works with ADK framework.
This will help us debug the hanging issue before fixing the main system.
"""

import asyncio
import os
import sys
from google.adk.agents import LlmAgent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioConnectionParams
from mcp.client.stdio import StdioServerParameters
from google.genai.types import Content, Part

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from department_of_market_intelligence import config
from department_of_market_intelligence.utils.model_loader import get_llm_model

def create_test_mcp_agent():
    """Create a test agent with MCP Desktop Commander toolset."""
    print("🧪 Creating MCP Desktop Commander toolset...")
    
    # Create MCP toolset inline as per ADK documentation
    toolset = MCPToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command=config.DESKTOP_COMMANDER_COMMAND,
                args=config.DESKTOP_COMMANDER_ARGS,
                cwd=project_root
            )
        )
    )
    
    print("✅ MCP toolset created, creating LLM agent...")
    
    # Use the exact same model configuration as the real project
    model = get_llm_model("gemini-2.5-pro")
    
    agent = LlmAgent(
        model=model,
        name="TestMCPAgent",
        instruction="""
        You are a test agent with access to MCP Desktop Commander tools.
        
        Your task: Use the list_directory tool to list files in the current directory.
        Call the list_directory function with path parameter set to the current directory.
        
        Be concise and direct in your responses.
        """,
        tools=[toolset]  # Wrap in list as required by ADK
    )
    
    print("✅ Test agent created successfully!")
    return agent

async def test_mcp_agent():
    """Test the MCP agent to verify it works."""
    print("🚀 Starting MCP Desktop Commander test...")
    
    try:
        # Create the agent
        agent = create_test_mcp_agent()
        
        # Set up services like in main_simple.py
        session_service = InMemorySessionService()
        
        # Create runner
        runner = Runner(
            agent=agent,
            app_name="MCPTest",
            session_service=session_service,
        )
        
        # Create session
        session = await session_service.create_session(
            app_name="MCPTest",
            user_id="tester"
        )
        
        print("📡 Running agent with MCP tools...")
        
        # Create test message
        message = Content(parts=[Part(text="Please test the MCP Desktop Commander tools as instructed.")])
        
        print("🔍 About to call runner.run_async - this is where the issue happens...")
        
        # Run the agent with verbose error handling
        response_count = 0
        try:
            async for event in runner.run_async(
                session_id=session.id,
                user_id=session.user_id,
                new_message=message
            ):
                response_count += 1
                print(f"📨 Received event: {type(event)} - {event}")
                if event.content and event.content.parts:
                    content = event.content.parts[0].text
                    print(f"Agent: {content}")
        except Exception as e:
            print(f"❌ Internal ADK error (not your endpoint): {e}")
            import traceback
            traceback.print_exc()
            print("\n🔍 This confirms the issue is BEFORE your endpoint is called!")
        
        print(f"✅ Agent completed successfully! Generated {response_count} events")
        
        # Check if test file was created
        test_file = os.path.join(project_root, 'mcp_test_output.txt')
        if os.path.exists(test_file):
            print("✅ Test file created successfully!")
            with open(test_file, 'r') as f:
                print(f"File contents: {f.read()}")
        else:
            print("⚠️  Test file not found, but agent ran without hanging")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function."""
    print("=" * 60)
    print("MCP DESKTOP COMMANDER + ADK INTEGRATION TEST")
    print("=" * 60)
    
    success = await test_mcp_agent()
    
    if success:
        print("\n🎉 SUCCESS: MCP Desktop Commander works with ADK!")
        print("Now we can apply this pattern to the main system.")
    else:
        print("\n💥 FAILED: MCP integration has issues that need debugging.")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())