# /department_of_market_intelligence/agents/validators_updated.py
"""
Example of validators updated to use SessionState model.
This demonstrates the migration approach for other agents.
"""

import asyncio
from typing import AsyncGenerator
from google.adk.agents import LlmAgent, BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from .. import config
from ..utils.callbacks import ensure_end_of_output
from ..utils.model_loader import get_llm_model
from ..utils.state_model import SessionState
from ..utils.state_adapter import StateAdapter, StateProxy


def get_junior_validator_agent_v2():
    """Updated junior validator that uses SessionState model."""
    # Use mock agent in dry run mode
    if config.DRY_RUN_MODE and config.DRY_RUN_SKIP_LLM:
        from ..tools.mock_llm_agent import create_mock_llm_agent
        return create_mock_llm_agent(name="Junior_Validator_V2")
    
    # Use mock tools in dry run mode
    if config.DRY_RUN_MODE:
        from ..tools.mock_tools import mock_desktop_commander_toolset
        tools = mock_desktop_commander_toolset
    else:
        tools = [desktop_commander_toolset]
        
    return LlmAgent(
        model=get_llm_model(config.VALIDATOR_MODEL),
        name="Junior_Validator_V2",
        instruction="""
        ### Persona ###
        You are a Junior Validator. Your sole focus is on identifying critical, show-stopping errors and potential edge cases. You are concise and to the point.
        Today's date is: {current_date?}

        ### Context & State ###
        You will be given the path to an artifact to validate in `state['artifact_to_validate']`.
        You will also be given the current validation version number in `state['validation_version']`.

        ### Task ###
        1.  Use the `read_file` tool to load the content of the artifact specified in {artifact_to_validate}.
        2.  Rigorously review the content for any glaring errors, logical fallacies, or unhandled edge cases.
        3.  If you find no critical issues, your critique should be a single sentence: "No critical issues found."
        4.  Use the `write_file` tool to save your critique to `outputs/junior_critique_v{validation_version}.md`.
        5.  State update will be handled automatically.

        ### Output Format ###
        You MUST end every response with "<end of output>".
        """,
        tools=tools,
        after_model_callback=ensure_end_of_output
    )


class MetaValidatorCheckAgentV2(BaseAgent):
    """Updated meta validator that uses SessionState model."""
    
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        # Get the session state - could be dict or SessionState
        raw_state = ctx.session.state
        
        # Convert to SessionState if needed
        if isinstance(raw_state, dict):
            # Legacy dict state - convert to SessionState
            session = StateAdapter.dict_to_session_state(raw_state, config.TASK_ID)
        elif isinstance(raw_state, SessionState):
            # Already SessionState
            session = raw_state
        else:
            # StateProxy or other wrapper
            session = raw_state._session if hasattr(raw_state, '_session') else None
            if not session:
                raise ValueError(f"Unknown state type: {type(raw_state)}")
        
        # Now use typed access
        status = session.get_validation_status()
        
        if status == "approved":
            print(f"META VALIDATOR V2: Status '{status}' - proceeding to next phase")
            should_escalate = True
        elif status == "critical_error":
            print(f"META VALIDATOR V2: Status '{status}' - escalating for replanning")
            # Set execution_status to trigger replanning at root level
            session.set_execution_status('critical_error')
            should_escalate = True
        else:  # rejected
            print(f"META VALIDATOR V2: Status '{status}' - continuing refinement loop")
            should_escalate = False
        
        # Update the state if it was a dict (for backward compatibility)
        if isinstance(raw_state, dict):
            # Write back changes
            updated_dict = StateAdapter.session_state_to_dict(session)
            ctx.session.state.update(updated_dict)
        
        # 'escalate=True' is the signal for a LoopAgent to terminate.
        yield Event(
            author=self.name,
            actions=EventActions(escalate=should_escalate)
        )
        # This is required for async generators, even if there's no real async work.
        await asyncio.sleep(0)


class SessionStateAwareAgent(BaseAgent):
    """Base class for agents that are aware of SessionState model.
    
    This provides utilities for handling both legacy dict state and new SessionState.
    """
    
    def get_session_state(self, ctx: InvocationContext) -> SessionState:
        """Get SessionState from context, converting if needed."""
        raw_state = ctx.session.state
        
        if isinstance(raw_state, SessionState):
            return raw_state
        elif isinstance(raw_state, dict):
            return StateAdapter.dict_to_session_state(raw_state, config.TASK_ID)
        elif hasattr(raw_state, '_session'):
            return raw_state._session
        else:
            raise ValueError(f"Unknown state type: {type(raw_state)}")
    
    def update_session_state(self, ctx: InvocationContext, session: SessionState) -> None:
        """Update the context with modified SessionState."""
        raw_state = ctx.session.state
        
        if isinstance(raw_state, SessionState):
            # Direct assignment should work
            ctx.session.state = session
        elif isinstance(raw_state, dict):
            # Convert back to dict and update
            updated_dict = StateAdapter.session_state_to_dict(session)
            ctx.session.state.clear()
            ctx.session.state.update(updated_dict)
        elif hasattr(raw_state, '_session'):
            # Update the wrapped session
            raw_state._session = session


# Example of a fully migrated agent
class SeniorValidatorV2(SessionStateAwareAgent):
    """Example of a fully migrated agent using SessionState."""
    
    def __init__(self, **kwargs):
        super().__init__(name="Senior_Validator_V2", **kwargs)
        self.tools = self._get_tools()
    
    def _get_tools(self):
        if config.DRY_RUN_MODE:
            from ..tools.mock_tools import mock_desktop_commander_toolset
            return mock_desktop_commander_toolset
        else:
            return [desktop_commander_toolset]
    
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        # Get typed session state
        session = self.get_session_state(ctx)
        
        # Access fields with type safety
        artifact_path = session.artifact_to_validate
        junior_critique = session.validation_info.junior_critique_artifact
        version = session.validation_info.validation_version
        
        print(f"SENIOR VALIDATOR V2: Reviewing {artifact_path} (v{version})")
        
        # Simulate validation logic
        if config.DRY_RUN_MODE:
            # Mock validation
            session.validation_info.senior_critique_artifact = f'outputs/senior_critique_v{version}.md'
            
            # Check execution status if present
            if session.get_execution_status() == 'critical_error':
                session.set_validation_status('critical_error')
                print(f"SENIOR VALIDATOR V2: Detected critical error - escalating")
            else:
                session.set_validation_status('approved')
                print(f"SENIOR VALIDATOR V2: Validation approved")
        else:
            # Real validation would happen here
            pass
        
        # Update the context with modified state
        self.update_session_state(ctx, session)
        
        yield Event(
            author=self.name,
            actions=EventActions()
        )


def demonstrate_migration_approach():
    """Show how to gradually migrate agents."""
    print("""
    Migration Approach:
    
    1. Start with wrapper approach (SessionStateAwareAgent)
       - Handles both dict and SessionState transparently
       - Minimal changes to agent logic
    
    2. Use StateProxy for dict-like access
       - Allows state['key'] syntax with SessionState backing
       - Good for complex agents with many state accesses
    
    3. Full migration to SessionState
       - Direct use of SessionState properties
       - Type safety and validation
       - Best performance
    
    4. Update instruction templates
       - Replace {state_key} with {session.field_name}
       - Or use a custom template processor
    """)