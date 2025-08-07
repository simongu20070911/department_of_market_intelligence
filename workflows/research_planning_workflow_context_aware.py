# /department_of_market_intelligence/workflows/research_planning_workflow_context_aware.py
"""Context-aware research planning workflow with intelligent validation."""

from google.adk.agents import SequentialAgent, LoopAgent, BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from typing import AsyncGenerator
import asyncio
import os
import re
from typing import Callable

from ..agents.chief_researcher import get_chief_researcher_agent
from ..agents.validators import (
    get_junior_validator_agent,
    get_senior_validator_agent,
    MetaValidatorCheckAgent,
    ParallelFinalValidationAgent
)
from ..utils.state_adapter import get_domi_state
from ..utils.validation_context import ValidationContextManager
from ..utils.phase_manager import WorkflowPhase, enhanced_phase_manager
from ..utils import directory_manager
from .. import config


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
        domi_state = get_domi_state(ctx)
        agent = self.agent_factory()
        
        async for event in agent.run_async(ctx):
            yield event
        
        if self.name == "ContextAwareChiefResearcher":
            import glob
            
            task_id = domi_state.task_id
            outputs_dir = config.get_outputs_dir(task_id)
            
            current_task = domi_state.current_task_description
            expected_version = domi_state.validation.validation_version
            
            if current_task == 'refine_plan':
                expected_plan = directory_manager.get_research_plan_path(task_id, expected_version)
                if os.path.exists(expected_plan):
                    domi_state.validation.plan_artifact_name = expected_plan
                    domi_state.validation.artifact_to_validate = expected_plan
                    print(f"📎 Wrapper found refined plan v{expected_version}: {os.path.basename(expected_plan)}")
                else:
                    print(f"⚠️  ERROR: Chief Researcher did not create expected plan v{expected_version}")
                    print(f"   Expected file: {expected_plan}")
                    plan_files = glob.glob(os.path.join(config.get_outputs_dir(task_id), "planning", "research_plan_v*.md"))
                    if plan_files:
                        def get_version_from_path(p):
                            match = re.search(r'_v(\d+)\.md', os.path.basename(p))
                            return int(match.group(1)) if match else -1
                        latest_plan = max(plan_files, key=get_version_from_path)
                        latest_version = get_version_from_path(latest_plan)
                        print(f"   Latest plan found: v{latest_version}")
                        domi_state.validation.validation_version = latest_version
                        domi_state.validation.plan_artifact_name = latest_plan
                        domi_state.validation.artifact_to_validate = latest_plan
            else:
                plan_files = glob.glob(os.path.join(config.get_outputs_dir(task_id), "planning", "research_plan_v*.md"))
                
                if plan_files:
                    def get_version_from_path(p):
                        match = re.search(r'_v(\d+)\.md', os.path.basename(p))
                        return int(match.group(1)) if match else -1

                    latest_plan = max(plan_files, key=get_version_from_path)
                    
                    domi_state.validation.plan_artifact_name = latest_plan
                    domi_state.validation.artifact_to_validate = latest_plan
                    print(f"📎 Wrapper found latest plan and set for validation: {os.path.basename(latest_plan)}")
                else:
                    print(f"⚠️  Wrapper could not find any research plan files in {outputs_dir}/planning/")
                    domi_state.validation.artifact_to_validate = "FILE_NOT_FOUND"

        if self.name == "ContextAwareOrchestrator":
            task_id = domi_state.task_id
            manifest_path = directory_manager.get_implementation_manifest_path(task_id)
            
            if os.path.exists(manifest_path):
                domi_state.execution.implementation_manifest_artifact = manifest_path
                domi_state.validation.artifact_to_validate = manifest_path
                print(f"📎 Wrapper confirmed manifest and set for validation: {os.path.basename(manifest_path)}")
            else:
                print(f"⚠️  Wrapper could not find the implementation manifest at {manifest_path}")
                domi_state.validation.artifact_to_validate = manifest_path


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
    max_iterations, _ = enhanced_phase_manager.get_parallel_config(WorkflowPhase.RESEARCH_REFINEMENT)
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
            domi_state = get_domi_state(ctx)
            current_phase = WorkflowPhase.from_string(domi_state.current_phase)
            if not current_phase or not current_phase.name.startswith('RESEARCH'):
                print(f"⚠️ ParallelValidationFeedbackLoop called in wrong phase: {current_phase.value if current_phase else 'unknown'}")
                print("   This workflow is for research planning only, not implementation manifest planning")
                return
            
            for iteration in range(self._max_parallel_iterations):
                print(f"\n🔄 [RESEARCH PLANNING] Parallel validation feedback iteration {iteration + 1}/{self._max_parallel_iterations}")
                
                async for event in planning_loop.run_async(ctx):
                    yield event
                
                async for event in parallel_validation.run_async(ctx):
                    yield event
                
                validation_status = domi_state.validation.validation_status
                consolidated_issues = domi_state.validation.consolidated_validation_issues
                
                if validation_status == 'critical_error' and consolidated_issues:
                    print(f"\n⚠️  Parallel validation found {len(consolidated_issues)} critical issues")
                    
                    task_id = domi_state.task_id
                    critiques_dir = os.path.dirname(directory_manager.get_critique_path(task_id, 0, "junior"))
                    
                    os.makedirs(critiques_dir, exist_ok=True)
                    
                    parallel_feedback_path = os.path.join(critiques_dir, "parallel_validation_feedback.md")
                    with open(parallel_feedback_path, 'w') as f:
                        f.write("# Parallel Validation Critical Issues\n\n")
                        f.write(f"Found {len(consolidated_issues)} critical issues from specialized validators:\n\n")
                        
                        issues_by_type = {}
                        for issue_str in consolidated_issues:
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
                    
                    domi_state.validation.validation_status = 'needs_revision_after_parallel_validation'
                    domi_state.validation.validation_context = 'research_plan'
                    domi_state.validation.revision_reason = 'parallel_validation_critical_issues'
                    domi_state.validation.parallel_validation_issues_count = len(consolidated_issues)
                    
                    if iteration < self._max_parallel_iterations - 1:
                        print("♻️  Re-running planning loop with parallel validation feedback...")
                        continue
                    else:
                        print("❌ Max parallel validation iterations reached")
                        break
                else:
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