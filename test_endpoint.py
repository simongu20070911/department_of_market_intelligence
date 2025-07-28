#!/usr/bin/env python3
"""
Test script to check if the custom LLM endpoint is working correctly.
"""

import requests
import json
import asyncio
import aiohttp

# Test configuration
ENDPOINT = "http://0.0.0.0:8000"
API_KEY = "sk-7m-daily-token-1"

def test_health_check():
    """Test if the endpoint is responding."""
    print("🔍 Testing endpoint health...")
    try:
        response = requests.get(f"{ENDPOINT}/health", timeout=10)
        print(f"Health check status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Endpoint is up and responding")
            return True
        else:
            print(f"⚠️  Endpoint returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_openai_format():
    """Test if the endpoint supports OpenAI chat completions format."""
    print("\n🔍 Testing OpenAI chat completions format...")
    
    url = f"{ENDPOINT}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "gemini-2.5-pro",
        "messages": [
            {"role": "user", "content": "Hello! Please respond with 'Test successful' if you can read this."}
        ],
        "max_tokens": 50,
        "temperature": 0.1
    }
    
    try:
        print(f"Making request to: {url}")
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ OpenAI format test successful!")
            print(f"Response: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Response body: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ OpenAI format test failed: {e}")
        return False

async def test_streaming():
    """Test if the endpoint supports streaming."""
    print("\n🔍 Testing streaming support...")
    
    url = f"{ENDPOINT}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "gemini-2.5-pro",
        "messages": [
            {"role": "user", "content": "Count from 1 to 5, one number per line."}
        ],
        "max_tokens": 100,
        "temperature": 0.1,
        "stream": True
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload, timeout=30) as response:
                print(f"Streaming response status: {response.status}")
                
                if response.status == 200:
                    print("✅ Streaming connection established")
                    chunk_count = 0
                    async for line in response.content:
                        if line:
                            chunk_count += 1
                            try:
                                line_str = line.decode('utf-8').strip()
                                if line_str.startswith('data: '):
                                    data = line_str[6:]  # Remove 'data: ' prefix
                                    if data != '[DONE]':
                                        chunk = json.loads(data)
                                        if 'choices' in chunk and chunk['choices']:
                                            content = chunk['choices'][0].get('delta', {}).get('content', '')
                                            if content:
                                                print(f"Chunk {chunk_count}: {repr(content)}")
                            except:
                                pass
                    
                    print(f"✅ Streaming test completed with {chunk_count} chunks")
                    return True
                else:
                    print(f"❌ Streaming failed with status {response.status}")
                    text = await response.text()
                    print(f"Response: {text}")
                    return False
                    
    except Exception as e:
        print(f"❌ Streaming test failed: {e}")
        return False

def test_litellm_integration():
    """Test using LiteLLM directly with the endpoint."""
    print("\n🔍 Testing LiteLLM integration...")
    
    try:
        from litellm import completion
        
        response = completion(
            model="openai/gemini-2.5-pro",
            messages=[{"role": "user", "content": "Say 'LiteLLM integration working' if you can read this."}],
            api_base=f"{ENDPOINT}/v1",
            api_key=API_KEY,
            timeout=30,
            max_tokens=50
        )
        
        print("✅ LiteLLM integration successful!")
        print(f"Response: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ LiteLLM integration failed: {e}")
        return False

async def main():
    """Run all endpoint tests."""
    print("=" * 60)
    print("CUSTOM LLM ENDPOINT TEST SUITE")
    print("=" * 60)
    print(f"Testing endpoint: {ENDPOINT}")
    print(f"Using API key: {API_KEY}")
    print("=" * 60)
    
    results = []
    
    # Test 1: Health check
    results.append(test_health_check())
    
    # Test 2: OpenAI format
    results.append(test_openai_format())
    
    # Test 3: Streaming
    results.append(await test_streaming())
    
    # Test 4: LiteLLM integration
    results.append(test_litellm_integration())
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    test_names = ["Health Check", "OpenAI Format", "Streaming", "LiteLLM Integration"]
    passed = sum(results)
    total = len(results)
    
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{i+1}. {name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your endpoint is working correctly.")
        return True
    else:
        print("💥 Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    asyncio.run(main())