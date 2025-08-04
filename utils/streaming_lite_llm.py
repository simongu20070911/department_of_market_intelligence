import uuid
import litellm
from google.adk.models.lite_llm import LiteLlm

class StreamingLiteLlm(LiteLlm):
    """Custom LiteLlm wrapper that adds streaming support and direct litellm calls."""
    
    def __init__(self, model: str, **kwargs):
        """Initialize with model and store litellm-specific parameters."""
        super().__init__(model=model)
        
        # Store litellm-specific parameters
        self.litellm_params = {
            "model": model,
            "api_key": kwargs.get("api_key"),
            "api_base": kwargs.get("api_base"),
            "stream": kwargs.get("stream", False),
            "timeout": kwargs.get("timeout"),
            "max_tokens": kwargs.get("max_tokens"),
            "extra_headers": kwargs.get("extra_headers"),
            "num_retries": kwargs.get("num_retries"),
            "retry_after": kwargs.get("retry_after"),
        }
        # Remove None values
        self.litellm_params = {k: v for k, v in self.litellm_params.items() if v is not None}
    
    async def acompletion(self, **kwargs):
        """Direct pass-through to litellm's acompletion function."""
        if "tools" in kwargs:
            for tool in kwargs["tools"]:
                if "function" in tool and "id" not in tool["function"]:
                    tool["function"]["id"] = str(uuid.uuid4())
        
        # Merge stored parameters with call-time parameters
        # Call-time parameters take precedence
        final_params = {**self.litellm_params, **kwargs}
        
        # Use litellm library directly
        return await litellm.acompletion(**final_params)