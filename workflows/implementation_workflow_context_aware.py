# /department_of_market_intelligence/workflows/implementation_workflow_context_aware.py
"""Context-aware implementation workflow with intelligent validation."""

import os
from typing import AsyncGenerator
from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event

from .research_planning_workflow_context_aware import (
    get_context_aware_orchestrator_workflow,
    get_context_aware_code_validation_workflow,
    get_context_aware_experiment_validation_workflow,
    get_context_aware_results_validation_workflow
)
from .coder_workflow import get_coder_workflow
from .experiment_workflow import get_experiment_workflow
from ..agents.orchestrator import get_orchestrator_agent
from ..agents.experiment_executor import get_experiment_executor_agent
from ..utils.state_adapter import get_domi_state, transition_to_next_phase
from ..utils.phase_manager import WorkflowPhase, enhanced_phase_manager
from ..utils.logger import get_logger
from .. import config

logger = get_logger(__name__)


class ImplementationWorkflowAgentContextAware(BaseAgent):
    """An implementation workflow that runs the appropriate sub-workflow based on the current phase."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._workflows = {
            "ORCHESTRATION": get_context_aware_orchestrator_workflow(),
            "CODING": get_coder_workflow(),
            "EXPERIMENT": get_experiment_workflow(),
            "RESULTS": get_context_aware_results_validation_workflow(),
        }

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        domi_state = get_domi_state(ctx)
        current_phase_name = WorkflowPhase.from_string(domi_state.current_phase).name
        
        workflow_key = current_phase_name.split('_')[0]
        workflow = self._workflows.get(workflow_key)

        if workflow:
            async for event in workflow.run_async(ctx):
                yield event
        else:
            logger.error(f"❌ No workflow found for phase: {current_phase_name}")