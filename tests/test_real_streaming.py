import asyncio
import litellm
from department_of_market_intelligence import config
from datetime import datetime

async def main():
    """Test streaming completion from the configured endpoint with a complex prompt."""
    
    # Set the custom endpoint and API key
    api_base = config.CUSTOM_GEMINI_API_ENDPOINT
    if not api_base.endswith("/v1"):
        api_base = f"{api_base.rstrip('/')}/v1"
    litellm.api_base = api_base
    litellm.api_key = config.CUSTOM_API_KEY
    
    model = f"openai/{config.AGENT_MODELS['CHIEF_RESEARCHER']}"
    # A more complex prompt to encourage a longer, multi-chunk response
    messages = [{"role": "user", "content": "Explain the concept of quantum entanglement in simple terms, as if you were explaining it to a high school student. Use an analogy to help illustrate the key ideas."}]
    
    print(f"--- Testing streaming completion for model: {model} ---")
    print(f"--- Endpoint: {litellm.api_base} ---")
    print(f"--- Prompt: {messages[0]['content']} ---")
    
    try:
        # Call the completion method with streaming enabled
        response = await litellm.acompletion(
            model=model,
            messages=messages,
            stream=True
        )
        
        # Print the streamed chunks with timestamps
        chunk_count = 0
        async for chunk in response:
            if chunk.choices[0].delta.content:
                chunk_count += 1
                timestamp = datetime.now().strftime('%H:%M:%S.%f')
                print(f"\n[CHUNK {chunk_count} - {timestamp}] ", end="")
                print(chunk.choices[0].delta.content, end="", flush=True)
        
        print(f"\n\n--- Streaming test completed successfully! Received {chunk_count} chunks. ---")
        
    except Exception as e:
        print(f"\n--- An error occurred during the streaming test: {e} ---")

if __name__ == "__main__":
    asyncio.run(main())