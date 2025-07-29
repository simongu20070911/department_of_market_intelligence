import asyncio
import pytest
import json
import os
from unittest.mock import MagicMock

from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from department_of_market_intelligence.workflows.coder_workflow import CoderWorkflowAgent
from department_of_market_intelligence import config

@pytest.mark.asyncio
async def test_thinking_tokens_are_streamed_with_real_api():
    """
    This test verifies that 'thinking' tokens are streamed from the LLM
    when running the CoderWorkflowAgent. It uses the real API.
    """
    # Arrange
    manifest_path = "/tmp/test_streaming_manifest.json"
    output_path = "/tmp/test_output.py"
    task = {
        "task_id": "streaming_test_task",
        "description": "A simple task to test streaming. Write a hello world function.",
        "dependencies": [],
        "input_artifacts": [],
        "output_artifacts": [output_path],
        "success_criteria": ["The file is created and contains a python function."]
    }

    # Correctly create a JSON array in the manifest
    with open(manifest_path, "w") as f:
        json.dump([task], f)

    # Mock the context and session state
    from google.adk.sessions import Session

    session = Session(
        id="test_session",
        app_name="test_app",
        user_id="test_user",
        state={"implementation_manifest_artifact": manifest_path},
    )
    
    agent = CoderWorkflowAgent(name="StreamingTestCoderWorkflow")

    from google.adk.sessions.base_session_service import BaseSessionService
    mock_session_service = MagicMock(spec=BaseSessionService)
    ctx = InvocationContext(
        session_service=mock_session_service,
        session=session,
        invocation_id="test_invocation",
        agent=agent,
    )

    # Store original config values
    original_coder_model = config.CODER_MODEL
    original_dry_run_mode = config.DRY_RUN_MODE
    original_skip_llm = config.DRY_RUN_SKIP_LLM

    # Configure for a real API call
    config.CODER_MODEL = "gemini/gemini-1.5-flash-latest"
    config.DRY_RUN_MODE = False
    config.DRY_RUN_SKIP_LLM = False

    # This is the fix for the streaming issue.
    # We will apply this *after* we have a failing test.
    # For now, we are testing the broken state.
    from department_of_market_intelligence.agents.coder import get_coder_agent
    
    # This is the agent to test
    # We need to patch the workflow to correctly parse the manifest



    thinking_found = False

    # Act
    try:
        print("\n--- Running Test: test_thinking_tokens_are_streamed_with_real_api ---")
        async for event in agent.run_async(ctx):
            if event.content and event.content.parts:
                text_chunk = event.content.parts[0].text
                print(f"LLM Event Received: {text_chunk}")
                if "thinking" in text_chunk.lower() or "thought" in text_chunk.lower():
                    thinking_found = True
                    print(">>> 'Thinking' token found in stream! <<<")
                    break
    finally:
        # Teardown
        if os.path.exists(manifest_path):
            os.remove(manifest_path)
        if os.path.exists(output_path):
            os.remove(output_path)
        
        # Restore original config and patched methods
        config.CODER_MODEL = original_coder_model
        config.DRY_RUN_MODE = original_dry_run_mode
        config.DRY_RUN_SKIP_LLM = original_skip_llm
        print("--- Test Finished ---")


    # Assert
    assert thinking_found, "No 'thinking' or 'thought' tokens were found in the streamed LLM chunks."