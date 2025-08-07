# /department_of_market_intelligence/workflows/results_workflow.py
"""Context-aware results workflow with intelligent validation."""

from google.adk.agents import SequentialAgent, LoopAgent, BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from typing import AsyncGenerator
import asyncio
import os
import re
from typing import Callable

from ..agents.coder import get_coder_agent
from ..agents.validators import (
    get_junior_validator_agent, 
    get_senior_validator_agent, 
    get_meta_validator_check_agent,
    ParallelFinalValidationAgent
)
from ..utils.state_adapter import get_domi_state
from ..utils.validation_context import ValidationContextManager
from ..utils.phase_manager import WorkflowPhase, enhanced_phase_manager
from ..utils import directory_manager
from ..utils.logger import get_logger
from .. import config

logger = get_logger(__name__)


class ContextAwareValidationWrapper(BaseAgent):
    """Wrapper that sets validation context before running validators."""
    
    validator_factory: Callable[[], BaseAgent]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._validator = None
    
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        domi_state = get_domi_state(ctx)
        # Detect and set validation context
        ctx.session.state = ValidationContextManager.prepare_validation_state(domi_state)
        
        # Log context detection
        artifact = domi_state.validation.artifact_to_validate or 'unknown'
        context = domi_state.validation.validation_context or 'unknown'
        confidence = domi_state.metadata.get('validation_confidence', 0.0)
        
        logger.info(f"\n🔍 VALIDATION CONTEXT DETECTION:")
        logger.info(f"   Artifact: {artifact}")
        logger.info(f"   Detected Context: {context}")
        logger.info(f"   Confidence: {confidence:.2%}")
        
        # Always create a new validator instance to prevent state leakage across loop iterations
        self._validator = self.validator_factory()
        
        # Run the validator with context-aware state
        async for event in self._validator.run_async(ctx):
            yield event


class ContextAwareAgentWrapper(BaseAgent):
    """
    Generic wrapper to create a fresh agent instance on each run.
    """
    
    agent_factory: Callable[[], BaseAgent]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        agent = self.agent_factory()
        async for event in agent.run_async(ctx):
            yield event


def get_context_aware_results_workflow():
    """Create results workflow with context-aware validation."""
    
    # Create context-aware validator wrappers
    junior_validator = ContextAwareValidationWrapper(
        validator_factory=get_junior_validator_agent,
        name="ContextAwareJuniorValidator"
    )
    
    senior_validator = ContextAwareValidationWrapper(
        validator_factory=get_senior_validator_agent,
        name="ContextAwareSeniorValidator"
    )
    
    # Wrap the coder to ensure it's recreated on each loop iteration
    coder_wrapper = ContextAwareAgentWrapper(
        agent_factory=get_coder_agent,
        name="ContextAwareCoder"
    )
    
    # Define the refinement sequence
    refinement_sequence = SequentialAgent(
        name="ResultsRefinementSequence",
        sub_agents=[
            coder_wrapper,
            junior_validator,
            senior_validator,
            get_meta_validator_check_agent(),
        ]
    )
    
    # Configure loop iterations
    max_iterations, _ = enhanced_phase_manager.get_parallel_config(WorkflowPhase.RESULTS_VALIDATION)
    if config.DRY_RUN_MODE:
        max_iterations = min(max_iterations, config.MAX_DRY_RUN_ITERATIONS)
        logger.info(f"DRY RUN MODE: Limiting results loop to {max_iterations} iterations")
    
    # Create the main refinement loop
    results_loop = LoopAgent(
        name="ResultsLoop",
        max_iterations=max_iterations,
        sub_agents=[refinement_sequence]
    )
    
    return SequentialAgent(
        name="ResultsWorkflow",
        sub_agents=[
            results_loop,
        ]
    )