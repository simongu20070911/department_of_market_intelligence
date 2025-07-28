# /department_of_market_intelligence/utils/model_loader.py

import os
from .. import config
from .streaming_lite_llm import StreamingLiteLlm

def get_llm_model(model_name: str):
    """
    Returns a StreamingLiteLlm instance configured for the custom endpoint.
    
    Supports both OpenAI and Gemini formats based on config toggle.
    """
    if config.VERBOSE_LOGGING:
        print(f"INFO: Using custom endpoint: {config.CUSTOM_GEMINI_API_ENDPOINT}")
        print(f"INFO: Using model: {model_name}")
        print(f"INFO: Using {'OpenAI' if config.USE_OPENAI_FORMAT else 'Gemini'} format")
    
    if config.USE_OPENAI_FORMAT:
        # Use OpenAI-compatible format
        openai_compatible_url = f"{config.CUSTOM_GEMINI_API_ENDPOINT}/openai/v1"
        os.environ["OPENAI_API_BASE"] = openai_compatible_url
        os.environ["OPENAI_API_KEY"] = config.CUSTOM_API_KEY
        
        return StreamingLiteLlm(
            model=f"openai/{model_name}",  # Use OpenAI format with custom server
            api_key=config.CUSTOM_API_KEY,
            stream=True,
            api_base=openai_compatible_url,
            extra_headers={
                "Authorization": f"Bearer {config.CUSTOM_API_KEY}",
                "Content-Type": "application/json"
            },
            num_retries=1,
            retry_after=1,
            timeout=60,
            max_tokens=8192,
        )
    else:
        # Use custom provider for Gemini format to bypass Google auth
        return StreamingLiteLlm(
            model=f"custom/{model_name}",  # Use custom provider to bypass authentication
            api_key=config.CUSTOM_API_KEY,
            stream=True,
            api_base=config.CUSTOM_GEMINI_API_ENDPOINT,
            num_retries=1,
            retry_after=1,
            timeout=60,
            max_tokens=8192,
        )