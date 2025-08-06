# /department_of_market_intelligence/workflows/research_planning_workflow_context_aware.py
"""Context-aware research planning workflow with intelligent validation."""

from google.adk.agents import SequentialAgent, LoopAgent, BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from typing import AsyncGenerator
import asyncio

from ..agents.chief_researcher import get_chief_researcher_agent
from ..agents.validators import (
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
        
        # Always create a new validator instance to prevent state leakage across loop iterations
        self._validator = self.validator_factory()
        
        # Run the validator with context-aware state
        async for event in self._validator.run_async(ctx):
            yield event


class ContextAwareAgentWrapper(BaseAgent):
    """
    Generic wrapper to create a fresh agent instance on each run.
    Crucially, after the agent runs, it finds the latest artifact on disk to set up
    the context for the next validation step, making the workflow robust against
    state-timing issues.
    """
    
    agent_factory: Callable[[], BaseAgent]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # No agent is created at init time
    
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        # Always create a new agent instance on each run to ensure a clean state
        agent = self.agent_factory()
        
        # Run the freshly created agent
        async for event in agent.run_async(ctx):
            yield event
        
        # After the agent runs, set the artifact for the next step (validation)
        # by finding the most recent file on disk. This is the most robust method.
        
        if self.name == "ContextAwareChiefResearcher":
            import glob
            import os
            import re
            
            task_id = ctx.session.state.get('task_id', config.TASK_ID)
            outputs_dir = config.get_outputs_dir(task_id)
            
            # Check if we just completed a refinement task
            current_task = ctx.session.state.get('current_task', '')
            expected_version = ctx.session.state.get('plan_version', 0)
            
            if current_task == 'refine_plan':
                # For refinement, look for the specific version that should have been created
                expected_plan = f"{outputs_dir}/planning/research_plan_v{expected_version}.md"
                if os.path.exists(expected_plan):
                    ctx.session.state['plan_artifact_name'] = expected_plan
                    ctx.session.state['artifact_to_validate'] = expected_plan
                    print(f"📎 Wrapper found refined plan v{expected_version}: {os.path.basename(expected_plan)}")
                else:
                    print(f"⚠️  ERROR: Chief Researcher did not create expected plan v{expected_version}")
                    print(f"   Expected file: {expected_plan}")
                    # Find what actually exists
                    plan_files = glob.glob(f"{outputs_dir}/planning/research_plan_v*.md")
                    if plan_files:
                        def get_version_from_path(p):
                            match = re.search(r'_v(\d+)\.md', os.path.basename(p))
                            return int(match.group(1)) if match else -1
                        latest_plan = max(plan_files, key=get_version_from_path)
                        latest_version = get_version_from_path(latest_plan)
                        print(f"   Latest plan found: v{latest_version}")
                        # Update state to reflect reality
                        ctx.session.state['plan_version'] = latest_version
                        ctx.session.state['plan_artifact_name'] = latest_plan
                        ctx.session.state['artifact_to_validate'] = latest_plan
            else:
                # For initial generation, find the latest plan
                plan_files = glob.glob(f"{outputs_dir}/planning/research_plan_v*.md")
                
                if plan_files:
                    # Find the latest plan by extracting the version number from the filename
                    def get_version_from_path(p):
                        match = re.search(r'_v(\d+)\.md', os.path.basename(p))
                        return int(match.group(1)) if match else -1

                    latest_plan = max(plan_files, key=get_version_from_path)
                    
                    ctx.session.state['plan_artifact_name'] = latest_plan
                    ctx.session.state['artifact_to_validate'] = latest_plan
                    print(f"📎 Wrapper found latest plan and set for validation: {os.path.basename(latest_plan)}")
                else:
                    # --- FIX: Prevent validator from running on a non-existent file ---
                    # This makes the point of failure much clearer.
                    print(f"⚠️  Wrapper could not find any research plan files in {outputs_dir}/planning/")
                    # Set a clear "not found" state instead of a path that will fail later
                    ctx.session.state['artifact_to_validate'] = "FILE_NOT_FOUND" 
                    # --- END FIX ---

        if self.name == "ContextAwareOrchestrator":
            # The orchestrator creates a single manifest file, so we can use a fixed path
            # but we ensure it's set correctly for the validator.
            import os
            task_id = ctx.session.state.get('task_id', config.TASK_ID)
            outputs_dir = config.get_outputs_dir(task_id)
            manifest_path = f"{outputs_dir}/planning/implementation_manifest.json"
            
            if os.path.exists(manifest_path):
                ctx.session.state['implementation_manifest_artifact'] = manifest_path
                ctx.session.state['artifact_to_validate'] = manifest_path
                print(f"📎 Wrapper confirmed manifest and set for validation: {os.path.basename(manifest_path)}")
            else:
                print(f"⚠️  Wrapper could not find the implementation manifest at {manifest_path}")
                # Set it anyway for the validator to report it's missing
                ctx.session.state['artifact_to_validate'] = manifest_path


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
    
    # Wrap the chief researcher to ensure it's recreated on each loop iteration
    chief_researcher_wrapper = ContextAwareAgentWrapper(
        agent_factory=get_chief_researcher_agent,
        name="ContextAwareChiefResearcher"
    )
    
    # Define the refinement sequence
    refinement_sequence = SequentialAgent(
        name="PlanRefinementSequence",
        sub_agents=[
            chief_researcher_wrapper,
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
    
    # A final check to ensure the status is correctly propagated after parallel validation
    final_status_check = MetaValidatorCheckAgent(name="FinalStatusCheck")

    # Create a wrapper that handles parallel validation feedback
    class ParallelValidationFeedbackLoop(BaseAgent):
        """Wrapper that feeds parallel validation results back to planning loop."""
        
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            # Store as a private attribute with underscore prefix
            self._max_parallel_iterations = 3
        
        async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
            for iteration in range(self._max_parallel_iterations):
                print(f"\n🔄 Parallel validation feedback iteration {iteration + 1}/{self._max_parallel_iterations}")
                
                # Run the planning loop
                async for event in planning_loop.run_async(ctx):
                    yield event
                
                # Run parallel validation
                async for event in parallel_validation.run_async(ctx):
                    yield event
                
                # Check parallel validation results
                validation_status = ctx.session.state.get('validation_status', '')
                consolidated_issues = ctx.session.state.get('consolidated_validation_issues', [])
                
                if validation_status == 'critical_error' and consolidated_issues:
                    print(f"\n⚠️  Parallel validation found {len(consolidated_issues)} critical issues")
                    
                    # Save consolidated issues to a file for Chief Researcher to read
                    task_id = ctx.session.state.get("task_id") or config.TASK_ID
                    outputs_dir = config.get_outputs_dir(task_id)
                    critiques_dir = f"{outputs_dir}/planning/critiques"
                    
                    # Create critiques directory if it doesn't exist
                    import os
                    os.makedirs(critiques_dir, exist_ok=True)
                    
                    # Write parallel validation feedback
                    parallel_feedback_path = f"{critiques_dir}/parallel_validation_feedback.md"
                    with open(parallel_feedback_path, 'w') as f:
                        f.write("# Parallel Validation Critical Issues\n\n")
                        f.write(f"Found {len(consolidated_issues)} critical issues from specialized validators:\n\n")
                        
                        # Group issues by validator type (issues are strings like "[validator_type] issue text")
                        issues_by_type = {}
                        for issue_str in consolidated_issues:
                            # Parse the validator type from the string format "[validator_type] issue text"
                            if isinstance(issue_str, str) and issue_str.startswith('['):
                                end_bracket = issue_str.find(']')
                                if end_bracket > 0:
                                    validator_type = issue_str[1:end_bracket]
                                    issue_text = issue_str[end_bracket+1:].strip()
                                else:
                                    validator_type = "Unknown"
                                    issue_text = issue_str
                            else:
                                validator_type = "Unknown"
                                issue_text = str(issue_str)
                            
                            if validator_type not in issues_by_type:
                                issues_by_type[validator_type] = []
                            issues_by_type[validator_type].append(issue_text)
                        
                        for validator_type, issues in issues_by_type.items():
                            f.write(f"## {validator_type} Issues\n\n")
                            for i, issue in enumerate(issues, 1):
                                f.write(f"{i}. {issue}\n")
                            f.write("\n")
                    
                    print(f"📝 Saved parallel validation feedback to {parallel_feedback_path}")
                    
                    # Reset validation status for next iteration
                    ctx.session.state['validation_status'] = 'needs_revision_after_parallel_validation'
                    ctx.session.state['validation_context'] = 'research_plan'
                    ctx.session.state['revision_reason'] = 'parallel_validation_critical_issues'
                    ctx.session.state['parallel_validation_issues_count'] = len(consolidated_issues)
                    
                    # Continue to next iteration if not at max
                    if iteration < self._max_parallel_iterations - 1:
                        print("♻️  Re-running planning loop with parallel validation feedback...")
                        continue
                    else:
                        print("❌ Max parallel validation iterations reached")
                        break
                else:
                    # Validation passed or no critical issues
                    print("✅ Parallel validation passed or no critical issues found")
                    break
            
            # Run final status check
            async for event in final_status_check.run_async(ctx):
                yield event
            
            yield Event(
                author=self.name,
                actions=EventActions()
            )
    
    # Use the feedback loop wrapper
    complete_planning_workflow = ParallelValidationFeedbackLoop(
        name="CompletePlanningWorkflowWithFeedback"
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
    
    # Wrap the orchestrator to ensure it's recreated on each loop iteration
    orchestrator_wrapper = ContextAwareAgentWrapper(
        agent_factory=get_orchestrator_agent,
        name="ContextAwareOrchestrator"
    )
    
    # Define the refinement sequence
    refinement_sequence = SequentialAgent(
        name="ManifestRefinementSequence",
        sub_agents=[
            orchestrator_wrapper,
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
    
    # Use standard LoopAgent but wrap it to set the flag when done
    orchestrator_loop = LoopAgent(
        name="OrchestratorPlanningLoop",
        max_iterations=max_iterations,
        sub_agents=[refinement_sequence]
    )
    
    # Create a wrapper that sets the max retries flag after the loop completes
    class LoopResultHandler(BaseAgent):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
        
        async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
            # Run the orchestrator loop
            async for event in orchestrator_loop.run_async(ctx):
                yield event
            
            # After loop completes, check if we need to set the max retries flag
            validation_status = ctx.session.state.get('validation_status', 'unknown')
            if validation_status != 'approved':
                print(f"⚠️  Orchestrator loop completed without approval - setting max retries flag")
                ctx.session.state['orchestrator_max_retries_reached'] = True
                ctx.session.state['orchestrator_iteration_count'] = max_iterations
    
    orchestrator_loop_with_fallback = LoopResultHandler(name="OrchestratorLoopHandler")
    
    # Create parallel final validation
    parallel_validation = ContextAwareValidationWrapper(
        validator_factory=lambda: ParallelFinalValidationAgent(name="ParallelFinalValidation"),
        name="ContextAwareParallelValidation"
    )
    
    # A final check to ensure the status is correctly propagated after parallel validation
    final_status_check = MetaValidatorCheckAgent(name="FinalStatusCheck")

    # Complete workflow
    complete_orchestrator_workflow = SequentialAgent(
        name="CompleteOrchestratorWorkflow",
        sub_agents=[
            orchestrator_loop_with_fallback,
            parallel_validation,
            final_status_check
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