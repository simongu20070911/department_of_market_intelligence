# /department_of_market_intelligence/utils/model_loader.py

import os
from google.adk.models.lite_llm import LiteLlm
from .. import config

def get_llm_model(model_name: str):
    """
    Returns a LiteLlm instance configured for the custom endpoint.
    
    The endpoint supports OpenAI format with streaming and thinking tokens.
    """
    print(f"INFO: Using custom endpoint: {config.CUSTOM_GEMINI_API_ENDPOINT}")
    print(f"INFO: Using model: {model_name}")
    print(f"INFO: Streaming and thinking tokens enabled")
    
    # Set the OpenAI base URL environment variable for LiteLLM
    os.environ["OPENAI_API_BASE"] = f"{config.CUSTOM_GEMINI_API_ENDPOINT}/v1"
    
    # LiteLLM will use the openai/ prefix to route to OpenAI-compatible endpoints
    # Since your server already supports OpenAI format, we just need to configure it properly
    return LiteLlm(
        model=f"openai/{model_name}",
        api_key=config.CUSTOM_API_KEY,
        # Enable streaming
        stream=True,
        # Set the base URL explicitly
        api_base=f"{config.CUSTOM_GEMINI_API_ENDPOINT}/v1",
    )