# /department_of_market_intelligence/workflows/research_planning_workflow_context_aware.py
"""Context-aware research planning workflow with intelligent validation."""

from google.adk.agents import SequentialAgent, LoopAgent, BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from typing import AsyncGenerator
import asyncio

from ..agents.chief_researcher import get_chief_researcher_agent
from ..agents.validators_context_aware import (
    get_junior_validator_agent, 
    get_senior_validator_agent, 
    MetaValidatorCheckAgent,
    ParallelFinalValidationAgent
)
from ..utils.validation_context import ValidationContextManager
from .. import config


from typing import Callable

class ContextAwareValidationWrapper(BaseAgent):
    """Wrapper that sets validation context before running validators."""
    
    validator_factory: Callable[[], BaseAgent]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._validator = None
    
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        # Detect and set validation context
        ctx.session.state = ValidationContextManager.prepare_validation_state(ctx.session.state)
        
        # Log context detection
        artifact = ctx.session.state.get('artifact_to_validate', 'unknown')
        context = ctx.session.state.get('validation_context', 'unknown')
        confidence = ctx.session.state.get('validation_confidence', 0.0)
        
        print(f"\n🔍 VALIDATION CONTEXT DETECTION:")
        print(f"   Artifact: {artifact}")
        print(f"   Detected Context: {context}")
        print(f"   Confidence: {confidence:.2%}")
        
        # Create validator if not exists
        if self._validator is None:
            self._validator = self.validator_factory()
        
        # Run the validator with context-aware state
        async for event in self._validator.run_async(ctx):
            yield event


def get_context_aware_research_planning_workflow():
    """Create research planning workflow with context-aware validation."""
    
    # Create context-aware validator wrappers
    junior_validator = ContextAwareValidationWrapper(
        validator_factory=get_junior_validator_agent,
        name="ContextAwareJuniorValidator"
    )
    
    senior_validator = ContextAwareValidationWrapper(
        validator_factory=get_senior_validator_agent,
        name="ContextAwareSeniorValidator"
    )
    
    # Define the refinement sequence
    refinement_sequence = SequentialAgent(
        name="PlanRefinementSequence",
        sub_agents=[
            get_chief_researcher_agent(),
            junior_validator,
            senior_validator,
            MetaValidatorCheckAgent(name="MetaValidatorCheck"),
        ]
    )
    
    # Configure loop iterations
    max_iterations = config.MAX_PLAN_REFINEMENT_LOOPS
    if config.DRY_RUN_MODE:
        max_iterations = min(max_iterations, config.MAX_DRY_RUN_ITERATIONS)
        print(f"DRY RUN MODE: Limiting planning loop to {max_iterations} iterations")
    
    # Create the main refinement loop
    planning_loop = LoopAgent(
        name="ResearchPlanningLoop",
        max_iterations=max_iterations,
        sub_agents=[refinement_sequence]
    )
    
    # Create parallel final validation with context awareness
    parallel_validation = ContextAwareValidationWrapper(
        validator_factory=lambda: ParallelFinalValidationAgent(name="ParallelFinalValidation"),
        name="ContextAwareParallelValidation"
    )
    
    # Complete workflow: loop + parallel validation
    complete_planning_workflow = SequentialAgent(
        name="CompletePlanningWorkflow",
        sub_agents=[
            planning_loop,
            parallel_validation
        ]
    )
    
    return complete_planning_workflow


def get_context_aware_orchestrator_workflow():
    """Create orchestrator workflow with context-aware validation."""
    
    # Import orchestrator here to avoid circular dependency
    from ..agents.orchestrator import get_orchestrator_agent
    
    # Create context-aware validator wrappers
    junior_validator = ContextAwareValidationWrapper(
        validator_factory=get_junior_validator_agent,
        name="ContextAwareJuniorValidator"
    )
    
    senior_validator = ContextAwareValidationWrapper(
        validator_factory=get_senior_validator_agent,
        name="ContextAwareSeniorValidator"
    )
    
    # Define the refinement sequence
    refinement_sequence = SequentialAgent(
        name="ManifestRefinementSequence",
        sub_agents=[
            get_orchestrator_agent(),
            junior_validator,
            senior_validator,
            MetaValidatorCheckAgent(name="MetaValidatorCheck"),
        ]
    )
    
    # Configure loop iterations
    max_iterations = config.MAX_ORCHESTRATOR_REFINEMENT_LOOPS
    if config.DRY_RUN_MODE:
        max_iterations = min(max_iterations, config.MAX_DRY_RUN_ITERATIONS)
        print(f"DRY RUN MODE: Limiting orchestrator loop to {max_iterations} iterations")
    
    # Create the main refinement loop
    orchestrator_loop = LoopAgent(
        name="OrchestratorPlanningLoop",
        max_iterations=max_iterations,
        sub_agents=[refinement_sequence]
    )
    
    # Create parallel final validation
    parallel_validation = ContextAwareValidationWrapper(
        validator_factory=lambda: ParallelFinalValidationAgent(name="ParallelFinalValidation"),
        name="ContextAwareParallelValidation"
    )
    
    # Complete workflow
    complete_orchestrator_workflow = SequentialAgent(
        name="CompleteOrchestratorWorkflow",
        sub_agents=[
            orchestrator_loop,
            parallel_validation
        ]
    )
    
    return complete_orchestrator_workflow


def get_context_aware_code_validation_workflow():
    """Create code validation workflow with context awareness."""
    
    # Create context-aware validators
    junior_validator = ContextAwareValidationWrapper(
        validator_factory=get_junior_validator_agent,
        name="ContextAwareJuniorValidator"
    )
    
    senior_validator = ContextAwareValidationWrapper(
        validator_factory=get_senior_validator_agent,
        name="ContextAwareSeniorValidator"
    )
    
    # Code validation sequence
    code_validation_sequence = SequentialAgent(
        name="CodeValidationSequence",
        sub_agents=[
            junior_validator,
            senior_validator,
            MetaValidatorCheckAgent(name="MetaValidatorCheck")
        ]
    )
    
    return code_validation_sequence


def get_context_aware_experiment_validation_workflow():
    """Create experiment execution validation workflow."""
    
    # Create context-aware validators
    junior_validator = ContextAwareValidationWrapper(
        validator_factory=get_junior_validator_agent,
        name="ContextAwareJuniorValidator"
    )
    
    senior_validator = ContextAwareValidationWrapper(
        validator_factory=get_senior_validator_agent,
        name="ContextAwareSeniorValidator"
    )
    
    # Experiment validation sequence
    experiment_validation_sequence = SequentialAgent(
        name="ExperimentValidationSequence",
        sub_agents=[
            junior_validator,
            senior_validator,
            MetaValidatorCheckAgent(name="MetaValidatorCheck")
        ]
    )
    
    return experiment_validation_sequence


def get_context_aware_results_validation_workflow():
    """Create results extraction validation workflow."""
    
    # Create context-aware validators
    junior_validator = ContextAwareValidationWrapper(
        validator_factory=get_junior_validator_agent,
        name="ContextAwareJuniorValidator"
    )
    
    senior_validator = ContextAwareValidationWrapper(
        validator_factory=get_senior_validator_agent,
        name="ContextAwareSeniorValidator"
    )
    
    # Results validation sequence with parallel final check
    results_validation_sequence = SequentialAgent(
        name="ResultsValidationSequence",
        sub_agents=[
            junior_validator,
            senior_validator,
            MetaValidatorCheckAgent(name="MetaValidatorCheck")
        ]
    )
    
    # Add parallel validation for final results
    parallel_validation = ContextAwareValidationWrapper(
        validator_factory=lambda: ParallelFinalValidationAgent(name="ParallelFinalValidation"),
        name="ContextAwareParallelValidation"
    )
    
    complete_results_workflow = SequentialAgent(
        name="CompleteResultsValidation",
        sub_agents=[
            results_validation_sequence,
            parallel_validation
        ]
    )
    
    return complete_results_workflow