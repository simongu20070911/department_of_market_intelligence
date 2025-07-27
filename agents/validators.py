# /department_of_market_intelligence/agents/validators.py
import asyncio
from typing import AsyncGenerator
from google.adk.agents import LlmAgent, BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from ..tools.desktop_commander import desktop_commander_toolset
from .. import config
from ..utils.callbacks import ensure_end_of_output
from ..utils.model_loader import get_llm_model

def get_junior_validator_agent():
    return LlmAgent(
        model=get_llm_model(config.VALIDATOR_MODEL),
        name="Junior_Validator",
        instruction="""
        ### Persona ###
        You are a Junior Validator. Your sole focus is on identifying critical, show-stopping errors and potential edge cases. You are concise and to the point.

        ### Context & State ###
        You will be given the path to an artifact to validate in `state['artifact_to_validate']`.
        You will also be given the current validation version number in `state['validation_version']`.

        ### Task ###
        1.  Use the `read_file` tool to load the content of the artifact specified in `state['artifact_to_validate']`.
        2.  Rigorously review the content for any glaring errors, logical fallacies, or unhandled edge cases.
        3.  If you find no critical issues, your critique should be a single sentence: "No critical issues found."
        4.  Use the `write_file` tool to save your critique to `outputs/junior_critique_v{+validation_version+}.md`.
        5.  Update the session state: `state['junior_critique_artifact'] = 'outputs/junior_critique_v{+validation_version+}.md'`.

        ### Output Format ###
        You MUST end every response with "<end of output>".
        """,
        tools=[desktop_commander_toolset],
        after_model_callback=ensure_end_of_output
    )

def get_senior_validator_agent():
    return LlmAgent(
        model=get_llm_model(config.VALIDATOR_MODEL),
        name="Senior_Validator",
        instruction="""
        ### Persona ###
        You are a Senior Validator. You provide detailed, constructive, and comprehensive analysis, building upon the junior validator's findings. Your judgment determines if a work product is ready.

        ### Context & State ###
        - Primary artifact to validate: `state['artifact_to_validate']`
        - Junior validator's critique: `state['junior_critique_artifact']`
        - Current validation version: `state['validation_version']`

        ### Task ###
        1.  Use `read_file` to load both the primary artifact and the junior critique.
        2.  Synthesize the junior's findings with your own in-depth analysis. Assess the work for methodological soundness, alignment with goals, and overall quality.
        3.  Use `write_file` to save your comprehensive critique to `outputs/senior_critique_v{+validation_version+}.md`.
        4.  Update the session state: `state['senior_critique_artifact'] = 'outputs/senior_critique_v{+validation_version+}.md'`.
        5.  **Crucially, you must make a final judgment.** Based on your analysis, set the session state key `state['validation_status']` to one of two exact string values: 'approved' or 'rejected'.

        ### Output Format ###
        You MUST end every response with "<end of output>".
        """,
        tools=[desktop_commander_toolset],
        after_model_callback=ensure_end_of_output
    )

# This is not an LLM agent. It's a simple control-flow agent.
class MetaValidatorCheckAgent(BaseAgent):
    """Checks the state for 'validation_status' and escalates to end a loop if approved."""
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        status = ctx.session.state.get("validation_status", "rejected")
        is_approved = (status == "approved")
        
        # 'escalate=True' is the signal for a LoopAgent to terminate.
        yield Event(
            author=self.name,
            actions=EventActions(escalate=is_approved)
        )
        # This is required for async generators, even if there's no real async work.
        await asyncio.sleep(0)