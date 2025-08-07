# /department_of_market_intelligence/workflows/validation_utils.py
"""
Utilities for creating validation workflows.
"""
from google.adk.agents import BaseAgent, LoopAgent, SequentialAgent
from google.adk.agents.invocation_context import InvocationContext
from ..agents.validators import get_junior_validator_agent, get_senior_validator_agent, get_meta_validator_check_agent
from ..utils.state_adapter import get_domi_state

def create_validation_loop(agent_to_validate: BaseAgent, loop_name: str) -> LoopAgent:
    """
    Creates a validation loop for a given agent.
    """
    validation_sequence = SequentialAgent(
        name=f"{loop_name}_ValidationSequence",
        sub_agents=[
            agent_to_validate,
            get_junior_validator_agent(),
            get_senior_validator_agent(),
            get_meta_validator_check_agent()
        ]
    )

    async def should_continue(ctx: InvocationContext) -> bool:
        domi_state = get_domi_state(ctx)
        validation_status = domi_state.validation.status
        
        if validation_status == "approved":
            return False
        if validation_status == "rejected":
            domi_state.validation.validation_version += 1
            return True
        return True

    return LoopAgent(
        name=loop_name,
        sub_agent=validation_sequence,
        should_continue=should_continue
    )