# /department_of_market_intelligence/utils/callbacks.py
from typing import Optional
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse
from .. import config

def ensure_end_of_output(
    *, callback_context: CallbackContext, llm_response: LlmResponse
) -> Optional[LlmResponse]:
    """Checks if the model response ends with the required marker."""
    try:
        text = None
        
        # Handle Gemini response structure
        if hasattr(llm_response, 'candidates') and llm_response.candidates:
            candidate = llm_response.candidates[0]
            if hasattr(candidate, 'content') and candidate.content:
                if hasattr(candidate.content, 'parts') and candidate.content.parts:
                    # Standard structure
                    text = candidate.content.parts[0].text
                elif hasattr(candidate.content, 'text'):
                    # Alternative structure
                    text = candidate.content.text
        
        if text and not text.strip().endswith(config.END_OF_OUTPUT_MARKER):
            print(f"WARNING: Output from model did not contain the required marker. Retrying may be necessary.")
            print(f"Output preview: {text[:100]}...")
            # In a production system, you might want to return a new LlmResponse
            # to force a retry or signal a failure.
    except Exception as e:
        print(f"WARNING: Error in callback processing response: {e}")
        # Log the response structure for debugging
        print(f"Response type: {type(llm_response)}")
        if hasattr(llm_response, 'candidates'):
            print(f"Has candidates: {bool(llm_response.candidates)}")
    return None # Allow the response to proceed