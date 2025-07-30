#!/usr/bin/env python3
"""
Use LiteLLM's built-in debug mode to see the exact requests.
"""

import asyncio
import sys
import os
import litellm

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from department_of_market_intelligence.test_mcp_agent import create_test_mcp_agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai.types import Content, Part

async def debug_with_litellm():
    """Enable LiteLLM debug mode to see exactly what's being sent."""
    print("🔍 LITELLM DEBUG MODE")
    print("=" * 50)
    
    # Enable LiteLLM debug mode
    litellm.set_verbose = True
    litellm._turn_on_debug()
    
    print("✅ LiteLLM debug mode enabled - you'll see all HTTP requests now")
    print("🚀 Creating test agent...")
    
    try:
        # Create agent with MCP tools
        agent = create_test_mcp_agent()
        
        # Set up services
        session_service = InMemorySessionService()
        runner = Runner(agent=agent, app_name="DebugTest", session_service=session_service)
        session = await session_service.create_session(app_name="DebugTest", user_id="debugger")
        
        message = Content(parts=[Part(text="Use list_directory tool to list files in current directory.")])
        
        print("📡 Running agent - watch for HTTP request details...")
        
        event_count = 0
        async for event in runner.run_async(
            session_id=session.id,
            user_id=session.user_id,
            new_message=message
        ):
            event_count += 1
            print(f"\n📨 Event {event_count}: {type(event)}")
            
            # Show event details
            if hasattr(event, 'content') and event.content:
                if hasattr(event.content, 'parts'):
                    for i, part in enumerate(event.content.parts):
                        if hasattr(part, 'function_call'):
                            print(f"  └─ Function call: {part.function_call.name}")
                        elif hasattr(part, 'function_response'):
                            print(f"  └─ Function response: {part.function_response.name}")
                        elif hasattr(part, 'text'):
                            print(f"  └─ Text: {part.text[:100]}...")
            
            if event_count >= 3:  # Prevent infinite loop
                break
        
    except Exception as e:
        print(f"\n❌ Expected error: {e}")
        print("The HTTP request details above show what your endpoint received!")

if __name__ == "__main__":
    asyncio.run(debug_with_litellm())