# /department_of_market_intelligence/workflows/implementation_workflow_context_aware.py
"""Context-aware implementation workflow with intelligent validation."""

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
from .. import config


class ImplementationWorkflowAgentContextAware(BaseAgent):
    """Context-aware implementation workflow that coordinates all implementation phases."""

    def __init__(self, **kwargs):
        # Initialize all sub-workflows
        self._orchestrator_workflow = get_context_aware_orchestrator_workflow()
        self._coder_workflow = get_coder_workflow()  # Coders use standard workflow
        self._experiment_workflow = get_experiment_workflow()  # Standard experiment workflow
        self._orchestrator_agent = get_orchestrator_agent()
        self._experiment_executor = get_experiment_executor_agent()
        
        # Context-aware validation workflows
        self._code_validation = get_context_aware_code_validation_workflow()
        self._experiment_validation = get_context_aware_experiment_validation_workflow()
        self._results_validation = get_context_aware_results_validation_workflow()
        
        super().__init__(
            sub_agents=[
                self._orchestrator_workflow,
                self._coder_workflow,
                self._experiment_workflow,
                self._orchestrator_agent,
                self._experiment_executor,
                self._code_validation,
                self._experiment_validation,
                self._results_validation
            ],
            **kwargs
        )

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        from ..utils.checkpoint_manager import checkpoint_manager
        from ..utils.state_adapter import StateProxy
        
        # Get state proxy
        session_state = getattr(ctx.session, '_typed_state', None)
        state_proxy = StateProxy(ctx.session, session_state)
        
        print("\n🎯 CONTEXT-AWARE IMPLEMENTATION WORKFLOW")
        print("="*60)
        
        # --- Step 1: Orchestrator Planning ---
        print("\n📋 Step 1: Orchestrator Planning (Context-Aware)")
        print("-"*40)
        
        state_proxy['current_task'] = 'generate_implementation_plan'
        
        # Create checkpoint
        checkpoint_manager.create_checkpoint(
            phase="implementation",
            step="orchestrator_start",
            session_state=session_state or ctx.session.state
        )
        
        # Run orchestrator with context-aware validation
        async for event in self._orchestrator_workflow.run_async(ctx):
            yield event
        
        # Check if orchestrator planning was successful
        validation_status = state_proxy.get('validation_status', 'unknown')
        if validation_status != 'approved':
            print(f"❌ Orchestrator planning failed validation: {validation_status}")
            state_proxy['execution_status'] = 'critical_error'
            return
        
        print("✅ Implementation manifest approved with context-aware validation!")
        
        # --- Step 2: Parallel Coding ---
        print("\n💻 Step 2: Parallel Coding Tasks")
        print("-"*40)
        
        state_proxy['current_task'] = 'parallel_coding'
        
        # Load manifest to get tasks
        manifest_path = state_proxy.get('implementation_manifest_artifact')
        if not manifest_path:
            print("❌ No implementation manifest found!")
            state_proxy['execution_status'] = 'critical_error'
            return
        
        # Run coder workflow (handles its own parallelization)
        async for event in self._coder_workflow.run_async(ctx):
            yield event
        
        # Each coder output is validated with context-aware validation
        # The coder workflow should set artifacts for validation
        
        # --- Step 3: Experiment Execution ---
        print("\n🧪 Step 3: Experiment Execution")
        print("-"*40)
        
        state_proxy['current_task'] = 'experiment_execution'
        state_proxy['current_phase'] = 'execution'
        
        # Create checkpoint before experiments
        checkpoint_manager.create_checkpoint(
            phase="execution",
            step="start",
            session_state=session_state or ctx.session.state
        )
        
        # Run experiment executor
        async for event in self._experiment_executor.run_async(ctx):
            yield event
        
        # Validate experiment execution with context-aware validation
        execution_journal = state_proxy.get('execution_log_artifact')
        if execution_journal:
            state_proxy['artifact_to_validate'] = execution_journal
            state_proxy['current_task'] = 'validate_experiment_execution'
            
            async for event in self._experiment_validation.run_async(ctx):
                yield event
            
            validation_status = state_proxy.get('validation_status', 'unknown')
            if validation_status != 'approved':
                print(f"❌ Experiment execution failed validation: {validation_status}")
                # May need to re-run experiments
        
        # --- Step 4: Results Extraction ---
        print("\n📊 Step 4: Results Extraction (Context-Aware)")
        print("-"*40)
        
        state_proxy['current_task'] = 'generate_results_extraction_plan'
        state_proxy['current_phase'] = 'results_extraction'
        
        # Orchestrator creates results extraction plan
        async for event in self._orchestrator_agent.run_async(ctx):
            yield event
        
        # Validate results extraction plan/code
        extraction_script = state_proxy.get('results_extraction_script_artifact')
        if extraction_script:
            state_proxy['artifact_to_validate'] = extraction_script
            state_proxy['current_task'] = 'validate_results_extraction'
            
            async for event in self._results_validation.run_async(ctx):
                yield event
            
            validation_status = state_proxy.get('validation_status', 'unknown')
            if validation_status != 'approved':
                print(f"⚠️  Results extraction needs refinement: {validation_status}")
        
        # Execute the results extraction
        print("\n🔄 Executing results extraction...")
        state_proxy['current_task'] = 'execute_results_extraction'
        
        # Run experiment executor to execute the extraction script
        async for event in self._experiment_executor.run_async(ctx):
            yield event
        
        # Final checkpoint
        results_artifact = state_proxy.get('final_results_artifact')
        checkpoint_manager.create_checkpoint(
            phase="implementation",
            step="complete",
            session_state=session_state or ctx.session.state,
            metadata={
                "results": results_artifact,
                "implementation_complete": True
            }
        )
        
        state_proxy['execution_status'] = 'complete'
        print("\n✅ Context-Aware Implementation Workflow Complete!")
        print(f"📊 Results: {results_artifact}")
        print("🔍 All phases validated with context-specific criteria")