#!/usr/bin/env python3
"""
Intercept the exact function_response payload that's causing the 500 error.
We know the first call works, so let's capture the second call that fails.
"""

import json
import asyncio
import sys
import os
from unittest.mock import patch
import requests
import time

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from department_of_market_intelligence.test_mcp_agent import create_test_mcp_agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai.types import Content, Part

# Global counter to track calls
call_counter = 0
captured_calls = []

def intercept_request(*args, **kwargs):
    """Intercept and examine the requests, especially the second one with function_response."""
    global call_counter, captured_calls
    call_counter += 1
    
    print(f"\n🔍 INTERCEPTED CALL #{call_counter}")
    print("=" * 60)
    
    # Get the payload
    payload = kwargs.get('json', {})
    
    # Check if this contains function_response (the problematic second call)
    messages = payload.get('messages', [])
    has_function_response = any(
        'function_response' in str(msg) for msg in messages
    )
    
    if has_function_response:
        print("🎯 THIS IS THE PROBLEMATIC FUNCTION_RESPONSE CALL!")
        print("This is what's causing your endpoint to return 500")
        
    print(f"📋 Messages count: {len(messages)}")
    for i, msg in enumerate(messages):
        print(f"  Message {i+1}: {msg.get('role', 'unknown')}")
        if 'function_call' in str(msg):
            print(f"    └─ Contains function_call")
        if 'function_response' in str(msg):
            print(f"    └─ Contains function_response ⚠️")
    
    # Show the tools schema
    tools = payload.get('tools', [])
    print(f"📦 Tools count: {len(tools)}")
    
    # Store the call
    captured_calls.append({
        'call_number': call_counter,
        'has_function_response': has_function_response,
        'payload': payload,
        'timestamp': time.time()
    })
    
    print("📝 Full payload:")
    print(json.dumps(payload, indent=2))
    print("=" * 60)
    
    # If this is the first call, let it succeed to see the function_call
    if call_counter == 1:
        print("✅ Allowing first call to proceed (should work)")
        # Call the real endpoint
        try:
            # Remove the mock and call the real thing
            import requests as real_requests
            real_response = real_requests.post(*args, **kwargs)
            print(f"First call result: {real_response.status_code}")
            if real_response.status_code == 200:
                response_data = real_response.json()
                print(f"LLM response: {json.dumps(response_data, indent=2)}")
            return real_response
        except Exception as e:
            print(f"First call failed: {e}")
    
    # For the second call (the problematic one), return a mock error
    print("❌ Blocking second call to prevent 500 error - we've captured what we need")
    
    class MockResponse:
        def __init__(self):
            self.status_code = 200  # Fake success to prevent crash
            self.text = '{"choices": [{"message": {"role": "assistant", "content": "DEBUG: Function response intercepted"}}]}'
            
        def json(self):
            return {
                "choices": [{
                    "message": {
                        "role": "assistant", 
                        "content": "DEBUG: Function response call intercepted for analysis"
                    }
                }]
            }
    
    return MockResponse()

async def test_and_intercept():
    """Run the test and intercept the function_response call."""
    print("🔍 FUNCTION_RESPONSE INTERCEPTOR")
    print("=" * 80)
    print("This will capture the exact payload causing your endpoint to return 500")
    print("=" * 80)
    
    try:
        # Create agent with MCP tools
        agent = create_test_mcp_agent()
        
        # Set up services
        session_service = InMemorySessionService()
        runner = Runner(agent=agent, app_name="DebugTest", session_service=session_service)
        session = await session_service.create_session(app_name="DebugTest", user_id="debugger")
        
        message = Content(parts=[Part(text="Please use the list_directory tool to list files in the current directory.")])
        
        # Patch requests to intercept
        with patch('requests.post', side_effect=intercept_request):
            print("🚀 Starting test that will trigger function_response...")
            
            event_count = 0
            async for event in runner.run_async(
                session_id=session.id,
                user_id=session.user_id,
                new_message=message
            ):
                event_count += 1
                print(f"📨 Event {event_count}: {type(event)}")
                if event_count >= 3:  # Limit to prevent infinite loop
                    break
        
        print(f"\n✅ Captured {len(captured_calls)} calls!")
        
        # Analyze the captures
        for call in captured_calls:
            if call['has_function_response']:
                print(f"\n🎯 ANALYSIS OF PROBLEMATIC CALL #{call['call_number']}:")
                print("This is the exact payload your endpoint can't handle:")
                print("-" * 50)
                
                messages = call['payload'].get('messages', [])
                for i, msg in enumerate(messages):
                    if 'function_response' in str(msg):
                        print(f"Function response message {i+1}:")
                        print(json.dumps(msg, indent=4))
                        break
        
    except Exception as e:
        print(f"Test completed with expected error: {e}")

if __name__ == "__main__":
    asyncio.run(test_and_intercept())