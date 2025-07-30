#!/usr/bin/env python3
"""
Debug script to intercept and examine exactly what ADK sends to the LLM endpoint
when MCP tools are included vs when they're not.
"""

import json
import asyncio
import sys
import os
from unittest.mock import patch
import requests

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from department_of_market_intelligence import config
from department_of_market_intelligence.test_mcp_agent import create_test_mcp_agent
from department_of_market_intelligence.utils.model_loader import get_llm_model

# Store captured requests
captured_requests = []

def capture_request(url, **kwargs):
    """Capture and log the request details."""
    print(f"\n🔍 INTERCEPTED REQUEST TO: {url}")
    print("=" * 80)
    
    # Capture headers
    headers = kwargs.get('headers', {})
    print("📋 HEADERS:")
    for key, value in headers.items():
        if 'auth' in key.lower() or 'key' in key.lower():
            print(f"  {key}: {'*' * len(value)}")  # Hide sensitive data
        else:
            print(f"  {key}: {value}")
    
    # Capture payload
    payload = kwargs.get('json', {})
    print("\n📦 PAYLOAD:")
    print(json.dumps(payload, indent=2))
    
    # Store for analysis
    captured_requests.append({
        'url': url,
        'headers': headers,
        'payload': payload,
        'method': kwargs.get('method', 'POST')
    })
    
    print("=" * 80)
    
    # Return a mock error to prevent actual call
    class MockResponse:
        def __init__(self):
            self.status_code = 500
            self.text = '{"error": {"code": "debug_intercepted", "message": "Request intercepted for debugging"}}'
            
        def json(self):
            return {"error": {"code": "debug_intercepted", "message": "Request intercepted for debugging"}}
    
    return MockResponse()

async def test_without_tools():
    """Test LLM call without any tools."""
    print("\n🧪 TEST 1: LLM Call WITHOUT Tools")
    print("=" * 50)
    
    # Create a simple model without tools
    from google.adk.models.lite_llm import LiteLlm
    from google.adk.agents import LlmAgent
    from google.adk.sessions import InMemorySessionService
    from google.adk.runners import Runner
    from google.genai.types import Content, Part
    
    model = get_llm_model("gemini-2.5-pro")
    
    agent = LlmAgent(
        model=model,
        name="NoToolsAgent",
        instruction="You are a test agent. Just say 'Hello without tools'.",
        tools=[]  # NO TOOLS
    )
    
    # Set up services
    session_service = InMemorySessionService()
    runner = Runner(agent=agent, app_name="DebugTest", session_service=session_service)
    session = await session_service.create_session(app_name="DebugTest", user_id="debugger")
    
    message = Content(parts=[Part(text="Please respond.")])
    
    try:
        # This should trigger a request without tools schema
        async for event in runner.run_async(
            session_id=session.id,
            user_id=session.user_id,
            new_message=message
        ):
            break  # Just capture the first request
    except Exception as e:
        print(f"Expected error (intercepted): {e}")

async def test_with_tools():
    """Test LLM call with MCP tools."""
    print("\n🧪 TEST 2: LLM Call WITH MCP Tools")
    print("=" * 50)
    
    try:
        # Create agent with MCP tools
        agent = create_test_mcp_agent()
        
        # Set up services
        from google.adk.sessions import InMemorySessionService
        from google.adk.runners import Runner
        from google.genai.types import Content, Part
        
        session_service = InMemorySessionService()
        runner = Runner(agent=agent, app_name="DebugTest", session_service=session_service)
        session = await session_service.create_session(app_name="DebugTest", user_id="debugger")
        
        message = Content(parts=[Part(text="Please respond.")])
        
        # This should trigger a request WITH tools schema
        async for event in runner.run_async(
            session_id=session.id,
            user_id=session.user_id,
            new_message=message
        ):
            break  # Just capture the first request
    except Exception as e:
        print(f"Expected error (intercepted): {e}")

def analyze_requests():
    """Analyze the captured requests."""
    print("\n📊 REQUEST ANALYSIS")
    print("=" * 50)
    
    if len(captured_requests) == 0:
        print("❌ No requests captured!")
        return
    
    for i, req in enumerate(captured_requests):
        print(f"\n🔍 REQUEST {i+1}:")
        print(f"   URL: {req['url']}")
        
        payload = req['payload']
        
        # Check if tools are present
        tools = payload.get('tools', [])
        print(f"   Tools count: {len(tools)}")
        
        if tools:
            print("   📋 TOOLS SCHEMA:")
            for j, tool in enumerate(tools[:2]):  # Show first 2 tools
                print(f"      Tool {j+1}: {json.dumps(tool, indent=6)}")
            if len(tools) > 2:
                print(f"      ... and {len(tools) - 2} more tools")
        
        # Check messages
        messages = payload.get('messages', [])
        print(f"   Messages count: {len(messages)}")
        
        # Check other important fields
        model = payload.get('model', 'not specified')
        print(f"   Model: {model}")
        
        stream = payload.get('stream', False)
        print(f"   Stream: {stream}")
        
        # Show full payload structure
        print(f"   📦 Payload keys: {list(payload.keys())}")

async def main():
    """Main debugging function."""
    print("🔍 LLM REQUEST INTERCEPTOR")
    print("=" * 80)
    print("This will capture and analyze the exact requests sent to your LLM endpoint")
    print("when MCP tools are vs aren't included.")
    print("=" * 80)
    
    # Patch the lower-level HTTP calls that LiteLLM uses
    with patch('requests.post', side_effect=capture_request):
        with patch('requests.request', side_effect=capture_request):
            with patch('httpx.post', side_effect=capture_request):
                with patch('httpx.request', side_effect=capture_request):
                    # Test without tools first
                    await test_without_tools()
                    
                    # Test with tools
                    await test_with_tools()
    
    # Analyze what we captured
    analyze_requests()
    
    print("\n✅ Debugging complete! Check the captured requests above.")

if __name__ == "__main__":
    asyncio.run(main())