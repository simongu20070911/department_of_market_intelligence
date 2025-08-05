# /department_of_market_intelligence/utils/model_loader.py
import os
from google.adk.models.lite_llm import LiteLlm  # Use ADK's built-in class
from .. import config

def get_llm_model(model_name: str):
    """
    Returns an ADK LiteLlm instance configured for your custom endpoint.
    This uses the standard ADK wrapper which correctly handles streaming.
    """
    if config.VERBOSE_LOGGING:
        print(f"INFO: Using custom endpoint: {config.CUSTOM_GEMINI_API_ENDPOINT}")
        print(f"INFO: Using model: {model_name}")

    api_base = config.CUSTOM_GEMINI_API_ENDPOINT
    if not api_base.endswith("/v1"):
        api_base = f"{api_base.rstrip('/')}/v1"

    # Since we're using an OpenAI-compatible endpoint (gemini-balance),
    # we need to use the openai provider format and set environment variables
    os.environ["OPENAI_API_BASE"] = api_base
    os.environ["OPENAI_API_KEY"] = config.CUSTOM_API_KEY
    
    # Use openai provider for OpenAI-compatible endpoints
    model_string = f"openai/{model_name}"

    return LiteLlm(
        model=model_string,
        api_key=config.CUSTOM_API_KEY,
        api_base=api_base,
        # Let the ADK Runner handle the stream=True parameter when needed.
        # Set other defaults for reliability.
        timeout=600,
        max_tokens=8192,
        num_retries=3,  # Increased to retry on transient failures
    )