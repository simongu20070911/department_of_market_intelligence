# /department_of_market_intelligence/utils/custom_model.py

"""
Custom model wrapper for Gemini endpoint with x-goog-api-key header
"""

import os
from typing import Any, Dict, Optional
from google.genai import Client
from google.genai.types import GenerateContentConfig
from google.adk.models import BaseGenerativeModel

class CustomGeminiModel(BaseGenerativeModel):
    """Custom model that uses x-goog-api-key header for authentication"""
    
    def __init__(self, model_name: str, endpoint_url: str, api_key: str):
        super().__init__()
        self.model_name = model_name
        self.endpoint_url = endpoint_url
        self.api_key = api_key
        
        # Set up the client with custom headers
        os.environ["GOOGLE_GENAI_BASE_URL"] = endpoint_url
        
        self.client = Client(
            api_key=api_key,
            http_options={
                'api_version': 'v1beta'
            }
        )
        
    async def generate_content(self, prompt: str, config: Optional[Dict[str, Any]] = None):
        """Generate content using the custom endpoint"""
        generation_config = GenerateContentConfig(
            temperature=config.get('temperature', 0.1) if config else 0.1,
            max_output_tokens=config.get('max_output_tokens', 4000) if config else 4000,
        )
        
        # Make the request with x-goog-api-key header
        response = await self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=generation_config,
            # The client should handle the x-goog-api-key header internally
        )
        
        return response
    
    async def generate_content_stream(self, prompt: str, config: Optional[Dict[str, Any]] = None):
        """Generate content with streaming"""
        generation_config = GenerateContentConfig(
            temperature=config.get('temperature', 0.1) if config else 0.1,
            max_output_tokens=config.get('max_output_tokens', 4000) if config else 4000,
        )
        
        # Stream the response
        async for chunk in self.client.models.generate_content_stream(
            model=self.model_name,
            contents=prompt,
            config=generation_config,
        ):
            yield chunk