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
        
        domi_state = get_domi_state(ctx)
        
        print("\n🎯 CONTEXT-AWARE IMPLEMENTATION WORKFLOW (MANIFEST PLANNING)")
        print("="*60)
        print("   This workflow handles implementation manifest planning and execution")
        print("   NOT to be confused with research planning workflow")
        
        # --- Step 1: Orchestrator Planning ---
        implementation_manifest_path = domi_state.execution.implementation_manifest_artifact
        validation_status = domi_state.validation.validation_status
        if implementation_manifest_path and os.path.exists(implementation_manifest_path) and validation_status.startswith('approved'):
            print(f"✅ Found approved implementation manifest (status: {validation_status}) from previous run: {os.path.basename(implementation_manifest_path)}")
            print("📋 Skipping orchestrator planning.")
            domi_state.validation.artifact_to_validate = implementation_manifest_path
        else:
            print("\n📋 Step 1: Orchestrator Planning (Context-Aware)")
            print("-"*40)
            
            domi_state.current_task_description = 'generate_implementation_plan'
            
            task_id = domi_state.task_id
            outputs_dir = config.get_outputs_dir(task_id)
            
            import glob
            plan_files = glob.glob(f"{outputs_dir}/planning/research_plan_v*.md")
            if plan_files:
                latest_plan = max(plan_files, key=lambda x: int(x.split('_v')[-1].split('.')[0]))
                domi_state.validation.plan_artifact_name = latest_plan
                print(f"📄 Found research plan: {latest_plan}")
            else:
                print("⚠️  No research plan found - validators may have limited context")
            
            domi_state.metadata['outputs_dir'] = outputs_dir
            domi_state.current_phase = WorkflowPhase.ORCHESTRATION_PLANNING.value
            print(f"🔧 Session state populated: task_id={task_id}, outputs_dir={outputs_dir}")
            
            checkpoint_manager.create_checkpoint(
                phase=WorkflowPhase.ORCHESTRATION_PLANNING.value,
                step="start",
                session_state=domi_state.to_checkpoint_dict()
            )
            
            async for event in self._orchestrator_workflow.run_async(ctx):
                yield event
            
            implementation_manifest_path = domi_state.execution.implementation_manifest_artifact
            if not implementation_manifest_path or not os.path.exists(implementation_manifest_path):
                print(f"❌ Implementation manifest not created at expected path: {implementation_manifest_path}")
                domi_state.execution.execution_status = 'critical_error'
                from google.adk.events import Event
                from google.genai.types import Content, Part
                yield Event(
                    author=self.name,
                    content=Content(parts=[Part(text="Implementation manifest creation failed")])
                )
                return
            
            validation_status = domi_state.validation.validation_status
            max_retries_reached = domi_state.metadata.get('domi_orchestrator_max_retries_reached', False)
            
            if validation_status != 'approved':
                if max_retries_reached and config.IMPLEMENTATION_MANIFEST_VALIDATION_ALLOW_PASS_ON_MAX_RETRIES:
                    print(f"⚠️  Implementation manifest validation failed after max retries: {validation_status}")
                    print(f"🎯 Config toggle enabled: continuing workflow despite validation failure")
                    print(f"📊 Iteration count: {domi_state.metadata.get('domi_orchestrator_iteration_count', 'unknown')}")
                    domi_state.validation.validation_status = 'approved_with_fallback'
                else:
                    print(f"❌ Orchestrator planning failed validation: {validation_status}")
                    if max_retries_reached:
                        print(f"❌ Max retries reached but fallback is disabled in config")
                    domi_state.execution.execution_status = 'critical_error'
                    from google.adk.events import Event
                    from google.genai.types import Content, Part
                    yield Event(
                        author=self.name,
                        content=Content(parts=[Part(text="Implementation workflow failed validation")])
                    )
                    return
            
            final_validation_status = domi_state.validation.validation_status
            if final_validation_status == 'approved_with_fallback':
                print("⚠️  Implementation manifest proceeding with fallback approval (max retries reached)")
            else:
                print("✅ Implementation manifest approved with context-aware validation!")
        
        checkpoint_manager.create_checkpoint(
            phase=WorkflowPhase.ORCHESTRATION_REFINEMENT.value,
            step="complete",
            session_state=domi_state.to_checkpoint_dict(),
            metadata={"manifest_path": domi_state.execution.implementation_manifest_artifact}
        )
        
        # --- Step 2: Parallel Coding ---
        print("\n💻 Step 2: Parallel Coding Tasks")
        print("-"*40)
        
        transition_to_next_phase(domi_state)
        domi_state.current_task_description = 'parallel_coding'
        
        manifest_path = domi_state.execution.implementation_manifest_artifact
        if not manifest_path:
            print("❌ No implementation manifest found!")
            domi_state.execution.execution_status = 'critical_error'
            from google.adk.events import Event
            from google.genai.types import Content, Part
            yield Event(
                author=self.name,
                content=Content(parts=[Part(text="No implementation manifest found")])
            )
            return
        
        try:
            async for event in self._coder_workflow.run_async(ctx):
                yield event
        except Exception as e:
            print(f"⚠️  Coder workflow error (non-fatal): {e}")
            domi_state.metadata['coder_status'] = 'partial_failure'
        
        # --- Step 3: Experiment Execution ---
        print("\n🧪 Step 3: Experiment Execution")
        print("-"*40)
        
        transition_to_next_phase(domi_state)
        domi_state.current_task_description = 'experiment_execution'
        
        checkpoint_manager.create_checkpoint(
            phase=WorkflowPhase.EXPERIMENT_SETUP.value,
            step="start",
            session_state=domi_state.to_checkpoint_dict()
        )
        
        async for event in self._experiment_executor.run_async(ctx):
            yield event
        
        execution_journal = domi_state.execution.execution_log_artifact
        if execution_journal:
            domi_state.validation.artifact_to_validate = execution_journal
            domi_state.current_task_description = 'validate_experiment_execution'
            
            async for event in self._experiment_validation.run_async(ctx):
                yield event
            
            validation_status = domi_state.validation.validation_status
            if validation_status != 'approved':
                print(f"❌ Experiment execution failed validation: {validation_status}")
        
        # --- Step 4: Results Extraction ---
        print("\n📊 Step 4: Results Extraction (Context-Aware)")
        print("-"*40)
        
        transition_to_next_phase(domi_state)
        domi_state.current_task_description = 'generate_results_extraction_plan'
        
        async for event in self._orchestrator_agent.run_async(ctx):
            yield event
        
        extraction_script = domi_state.execution.results_extraction_script_artifact
        if extraction_script:
            domi_state.validation.artifact_to_validate = extraction_script
            domi_state.current_task_description = 'validate_results_extraction'
            
            async for event in self._results_validation.run_async(ctx):
                yield event
            
            validation_status = domi_state.validation.validation_status
            if validation_status != 'approved':
                print(f"⚠️  Results extraction needs refinement: {validation_status}")
        
        print("\n🔄 Executing results extraction...")
        domi_state.current_task_description = 'execute_results_extraction'
        
        async for event in self._experiment_executor.run_async(ctx):
            yield event
        
        results_artifact = domi_state.execution.final_results_artifact
        checkpoint_manager.create_checkpoint(
            phase=WorkflowPhase.RESULTS_VALIDATION.value,
            step="complete",
            session_state=domi_state.to_checkpoint_dict(),
            metadata={
                "results": results_artifact,
                "implementation_complete": True
            }
        )
        
        domi_state.execution.execution_status = 'complete'
        print("\n✅ Context-Aware Implementation Workflow Complete!")
        print(f"📊 Results: {results_artifact}")
        print("🔍 All phases validated with context-specific criteria")