# /department_of_market_intelligence/agents/chief_researcher.py
import asyncio
import os
import json
from typing import Dict, Any, List, AsyncGenerator
from google.adk.agents import BaseAgent
from google.adk.agents.llm_agent import LlmAgent, ReadonlyContext
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai.types import Content, Part

from .. import config
from ..utils.callbacks import ensure_end_of_output
from ..utils.model_loader import get_llm_model
from ..utils.state_adapter import get_domi_state, update_session_state
from ..utils.checkpoint_manager import CheckpointManager
from ..prompts.definitions.chief_researcher import CHIEF_RESEARCHER_INSTRUCTION
from ..prompts.components.chief_researcher_tasks import GENERATE_INITIAL_PLAN_GUIDANCE


class ChiefResearcherAgent(BaseAgent):
    """Chief Researcher agent that creates the initial research plan."""

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        from ..tools.toolset_registry import toolset_registry
        from ..prompts.builder import inject_template_variables_with_context_preloading
        
        domi_state = get_domi_state(ctx)
        task_id = domi_state.task_id
        output_dir = config.get_outputs_dir(task_id)
        planning_dir = os.path.join(output_dir, "planning")
        plan_artifact_name = f"research_plan_v0.md"
        plan_path = os.path.join(planning_dir, plan_artifact_name)

        # Create the planning directory and the research plan using an LlmAgent
        toolset = toolset_registry.get_desktop_commander_toolset()
        
        # Define instruction provider that injects template variables
        def instruction_provider(inner_ctx: ReadonlyContext) -> str:
            base_instruction = inject_template_variables_with_context_preloading(
                CHIEF_RESEARCHER_INSTRUCTION, inner_ctx, "Chief_Researcher"
            )
            # Add explicit task guidance - be very clear about what needs to be done
            task_guidance = GENERATE_INITIAL_PLAN_GUIDANCE.format(
                planning_dir=planning_dir,
                plan_path=plan_path
            )
            return base_instruction + task_guidance
        
        # Use an LlmAgent with the instruction provider
        llm_agent = LlmAgent(
            model=get_llm_model(config.AGENT_MODELS["CHIEF_RESEARCHER"]),
            name="Chief_Researcher_Llm",
            instruction=instruction_provider,
            tools=[toolset],
            after_model_callback=ensure_end_of_output
        )
        async for event in llm_agent.run_async(ctx):
            yield event
        
        update_session_state(
            ctx,
            plan_artifact_name=plan_artifact_name,
            artifact_to_validate=plan_path
        )


def get_chief_researcher_agent():
    """Create Chief Researcher agent."""
    return ChiefResearcherAgent(name="Chief_Researcher")