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
from ..utils.phase_manager import WorkflowPhase, enhanced_phase_manager
from .. import config


class ImplementationWorkflowAgentContextAware(BaseAgent):
    """Context-aware implementation workflow that coordinates all implementation phases."""

    def __init__(self, **kwargs):
        # Initialize all sub-workflows
        orchestrator_workflow = get_context_aware_orchestrator_workflow()
        coder_workflow = get_coder_workflow()
        experiment_workflow = get_experiment_workflow()
        orchestrator_agent = get_orchestrator_agent()
        experiment_executor = get_experiment_executor_agent()
        
        # Context-aware validation workflows
        code_validation = get_context_aware_code_validation_workflow()
        experiment_validation = get_context_aware_experiment_validation_workflow()
        results_validation = get_context_aware_results_validation_workflow()
        
        super().__init__(
            sub_agents=[
                orchestrator_workflow,
                coder_workflow,
                experiment_workflow,
                orchestrator_agent,
                experiment_executor,
                code_validation,
                experiment_validation,
                results_validation
            ],
            **kwargs
        )
        
        self._orchestrator_workflow = orchestrator_workflow
        self._coder_workflow = coder_workflow
        self._experiment_workflow = experiment_workflow
        self._orchestrator_agent = orchestrator_agent
        self._experiment_executor = experiment_executor
        self._code_validation = code_validation
        self._experiment_validation = experiment_validation
        self._results_validation = results_validation

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        from ..utils.checkpoint_manager import checkpoint_manager
        
        # Use simple ADK state access patterns
        
        print("\n🎯 CONTEXT-AWARE IMPLEMENTATION WORKFLOW (MANIFEST PLANNING)")
        print("="*60)
        print("   This workflow handles implementation manifest planning and execution")
        print("   NOT to be confused with research planning workflow")
        
        # --- Step 1: Orchestrator Planning ---
        implementation_manifest_path = ctx.session.state.get('domi_implementation_manifest_artifact')
        # Check if an approved manifest already exists from a previous (or resumed) run
        validation_status = ctx.session.state.get('domi_validation_status', '')
        if implementation_manifest_path and os.path.exists(implementation_manifest_path) and validation_status.startswith('approved'):
            print(f"✅ Found approved implementation manifest (status: {validation_status}) from previous run: {os.path.basename(implementation_manifest_path)}")
            print("📋 Skipping orchestrator planning.")
            # Ensure the manifest path is correctly set for the next step
            ctx.session.state['domi_artifact_to_validate'] = implementation_manifest_path
        else:
            print("\n📋 Step 1: Orchestrator Planning (Context-Aware)")
            print("-"*40)
            
            ctx.session.state['domi_current_task'] = 'generate_implementation_plan'
            
            # Set task context for validation detection
            task_id = ctx.session.state.get('domi_task_id', config.TASK_ID)
            outputs_dir = config.get_outputs_dir(task_id)
            
            # Set the research plan path for validators to reference
            # Look for the latest research plan version
            import glob
            plan_files = glob.glob(f"{outputs_dir}/planning/research_plan_v*.md")
            if plan_files:
                latest_plan = max(plan_files, key=lambda x: int(x.split('_v')[-1].split('.')[0]))
                ctx.session.state['domi_plan_artifact_name'] = latest_plan
                print(f"📄 Found research plan: {latest_plan}")
            else:
                print("⚠️  No research plan found - validators may have limited context")
            
            # Ensure basic session state is populated for nested workflows
            ctx.session.state['domi_task_id'] = task_id
            ctx.session.state['domi_outputs_dir'] = outputs_dir
            ctx.session.state['domi_current_phase'] = WorkflowPhase.ORCHESTRATION_PLANNING.value
            print(f"🔧 Session state populated: task_id={task_id}, outputs_dir={outputs_dir}")
            
            # Don't pre-set artifact_to_validate - let orchestrator set it after creating the file
            # The validation context will be detected based on current_task
            
            # Create checkpoint
            checkpoint_manager.create_checkpoint(
                phase=WorkflowPhase.ORCHESTRATION_PLANNING.value,
                step="start",
                session_state=ctx.session.state
            )
            
            # Run orchestrator with context-aware validation
            async for event in self._orchestrator_workflow.run_async(ctx):
                yield event
            
            # Verify the manifest was actually created
            implementation_manifest_path = ctx.session.state.get('domi_implementation_manifest_artifact')
            if not implementation_manifest_path or not os.path.exists(implementation_manifest_path):
                print(f"❌ Implementation manifest not created at expected path: {implementation_manifest_path}")
                ctx.session.state['domi_execution_status'] = 'critical_error'
                from google.adk.events import Event
                from google.genai.types import Content, Part
                yield Event(
                    author=self.name,
                    content=Content(parts=[Part(text="Implementation manifest creation failed")])
                )
                return
            
            # Re-initialize the state proxy to get the latest state
            # Continue with simple state access
            
            # Check if orchestrator planning was successful
            # Directly access the state dictionary, bypassing the proxy which might be stale.
            validation_status = ctx.session.state.get('domi_validation_status', 'unknown')
            max_retries_reached = ctx.session.state.get('domi_orchestrator_max_retries_reached', False)
            
            if validation_status != 'approved':
                # Check if we should use fallback behavior
                if max_retries_reached and config.IMPLEMENTATION_MANIFEST_VALIDATION_ALLOW_PASS_ON_MAX_RETRIES:
                    print(f"⚠️  Implementation manifest validation failed after max retries: {validation_status}")
                    print(f"🎯 Config toggle enabled: continuing workflow despite validation failure")
                    print(f"📊 Iteration count: {ctx.session.state.get('domi_orchestrator_iteration_count', 'unknown')}")
                    # Set a warning status but allow continuation
                    ctx.session.state['domi_validation_status'] = 'approved_with_fallback'
                else:
                    print(f"❌ Orchestrator planning failed validation: {validation_status}")
                    if max_retries_reached:
                        print(f"❌ Max retries reached but fallback is disabled in config")
                    ctx.session.state['domi_execution_status'] = 'critical_error'
                    # Need to yield something to make this an async generator
                    from google.adk.events import Event
                    from google.genai.types import Content, Part
                    yield Event(
                        author=self.name,
                        content=Content(parts=[Part(text="Implementation workflow failed validation")])
                    )
                    return
            
            # Update success message based on validation status
            final_validation_status = ctx.session.state.get('domi_validation_status', 'unknown')
            if final_validation_status == 'approved_with_fallback':
                print("⚠️  Implementation manifest proceeding with fallback approval (max retries reached)")
            else:
                print("✅ Implementation manifest approved with context-aware validation!")
        
        # Create a checkpoint after the orchestrator has successfully planned and been validated.
        # This prevents re-running the orchestrator if the workflow is interrupted later.
        checkpoint_manager.create_checkpoint(
            phase=WorkflowPhase.ORCHESTRATION_REFINEMENT.value,
            step="complete",
            session_state=ctx.session.state,
            metadata={"manifest_path": ctx.session.state.get('domi_implementation_manifest_artifact')}
        )
        
        # --- Step 2: Parallel Coding ---
        print("\n💻 Step 2: Parallel Coding Tasks")
        print("-"*40)
        
        ctx.session.state['domi_current_phase'] = WorkflowPhase.CODING_ASSIGNMENT.value
        ctx.session.state['domi_current_task'] = 'parallel_coding'
        
        # Load manifest to get tasks
        manifest_path = ctx.session.state.get('domi_implementation_manifest_artifact')
        if not manifest_path:
            print("❌ No implementation manifest found!")
            ctx.session.state['domi_execution_status'] = 'critical_error'
            # Need to yield something to make this an async generator
            from google.adk.events import Event
            from google.genai.types import Content, Part
            yield Event(
                author=self.name,
                content=Content(parts=[Part(text="No implementation manifest found")])
            )
            return
        
        # Run coder workflow (handles its own parallelization)
        try:
            async for event in self._coder_workflow.run_async(ctx):
                yield event
        except Exception as e:
            print(f"⚠️  Coder workflow error (non-fatal): {e}")
            # Don't set critical_error - allow workflow to continue
            # The experiment executor can still run with existing code
            ctx.session.state['domi_coder_status'] = 'partial_failure'
        
        # Each coder output is validated with context-aware validation
        # The coder workflow should set artifacts for validation
        
        # --- Step 3: Experiment Execution ---
        print("\n🧪 Step 3: Experiment Execution")
        print("-"*40)
        
        ctx.session.state['domi_current_phase'] = WorkflowPhase.EXPERIMENT_SETUP.value
        ctx.session.state['domi_current_task'] = 'experiment_execution'
        
        # Create checkpoint before experiments
        checkpoint_manager.create_checkpoint(
            phase=WorkflowPhase.EXPERIMENT_SETUP.value,
            step="start",
            session_state=ctx.session.state
        )
        
        # Run experiment executor
        async for event in self._experiment_executor.run_async(ctx):
            yield event
        
        # Validate experiment execution with context-aware validation
        execution_journal = ctx.session.state.get('domi_execution_log_artifact')
        if execution_journal:
            ctx.session.state['domi_artifact_to_validate'] = execution_journal
            ctx.session.state['domi_current_task'] = 'validate_experiment_execution'
            
            async for event in self._experiment_validation.run_async(ctx):
                yield event
            
            validation_status = ctx.session.state.get('domi_validation_status', 'unknown')
            if validation_status != 'approved':
                print(f"❌ Experiment execution failed validation: {validation_status}")
                # May need to re-run experiments
        
        # --- Step 4: Results Extraction ---
        print("\n📊 Step 4: Results Extraction (Context-Aware)")
        print("-"*40)
        
        ctx.session.state['domi_current_phase'] = WorkflowPhase.RESULTS_PLANNING.value
        ctx.session.state['domi_current_task'] = 'generate_results_extraction_plan'
        
        # Orchestrator creates results extraction plan
        async for event in self._orchestrator_agent.run_async(ctx):
            yield event
        
        # Validate results extraction plan/code
        extraction_script = ctx.session.state.get('domi_results_extraction_script_artifact')
        if extraction_script:
            ctx.session.state['domi_artifact_to_validate'] = extraction_script
            ctx.session.state['domi_current_task'] = 'validate_results_extraction'
            
            async for event in self._results_validation.run_async(ctx):
                yield event
            
            validation_status = ctx.session.state.get('domi_validation_status', 'unknown')
            if validation_status != 'approved':
                print(f"⚠️  Results extraction needs refinement: {validation_status}")
        
        # Execute the results extraction
        print("\n🔄 Executing results extraction...")
        ctx.session.state['domi_current_task'] = 'execute_results_extraction'
        
        # Run experiment executor to execute the extraction script
        async for event in self._experiment_executor.run_async(ctx):
            yield event
        
        # Final checkpoint
        results_artifact = ctx.session.state.get('domi_final_results_artifact')
        checkpoint_manager.create_checkpoint(
            phase=WorkflowPhase.RESULTS_VALIDATION.value,
            step="complete",
            session_state=ctx.session.state,
            metadata={
                "results": results_artifact,
                "implementation_complete": True
            }
        )
        
        ctx.session.state['domi_execution_status'] = 'complete'
        print("\n✅ Context-Aware Implementation Workflow Complete!")
        print(f"📊 Results: {results_artifact}")
        print("🔍 All phases validated with context-specific criteria")