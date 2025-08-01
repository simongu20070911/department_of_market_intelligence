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
        
        print("\n🎯 CONTEXT-AWARE IMPLEMENTATION WORKFLOW")
        print("="*60)
        
        # --- Step 1: Orchestrator Planning ---
        print("\n📋 Step 1: Orchestrator Planning (Context-Aware)")
        print("-"*40)
        
        ctx.session.state['current_task'] = 'generate_implementation_plan'
        
        # Create checkpoint
        checkpoint_manager.create_checkpoint(
            phase="implementation",
            step="orchestrator_start",
            session_state=session_state or ctx.session.state
        )
        
        # Run orchestrator with context-aware validation
        async for event in self._orchestrator_workflow.run_async(ctx):
            yield event
        
        # Re-initialize the state proxy to get the latest state
        # Continue with simple state access
        
        # Check if orchestrator planning was successful
        # Directly access the state dictionary, bypassing the proxy which might be stale.
        validation_status = ctx.session.state.get('validation_status', 'unknown')
        if validation_status != 'approved':
            print(f"❌ Orchestrator planning failed validation: {validation_status}")
            ctx.session.state['execution_status'] = 'critical_error'
            # Need to yield something to make this an async generator
            from google.adk.events import Event
            from google.genai.types import Content, Part
            yield Event(
                author=self.name,
                content=Content(parts=[Part(text="Implementation workflow failed validation")])
            )
            return
        
        print("✅ Implementation manifest approved with context-aware validation!")
        
        # --- Step 2: Parallel Coding ---
        print("\n💻 Step 2: Parallel Coding Tasks")
        print("-"*40)
        
        ctx.session.state['current_task'] = 'parallel_coding'
        
        # Load manifest to get tasks
        manifest_path = ctx.session.state.get('implementation_manifest_artifact')
        if not manifest_path:
            print("❌ No implementation manifest found!")
            ctx.session.state['execution_status'] = 'critical_error'
            # Need to yield something to make this an async generator
            from google.adk.events import Event
            from google.genai.types import Content, Part
            yield Event(
                author=self.name,
                content=Content(parts=[Part(text="No implementation manifest found")])
            )
            return
        
        # Run coder workflow (handles its own parallelization)
        async for event in self._coder_workflow.run_async(ctx):
            yield event
        
        # Each coder output is validated with context-aware validation
        # The coder workflow should set artifacts for validation
        
        # --- Step 3: Experiment Execution ---
        print("\n🧪 Step 3: Experiment Execution")
        print("-"*40)
        
        ctx.session.state['current_task'] = 'experiment_execution'
        ctx.session.state['current_phase'] = 'execution'
        
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
        execution_journal = ctx.session.state.get('execution_log_artifact')
        if execution_journal:
            ctx.session.state['artifact_to_validate'] = execution_journal
            ctx.session.state['current_task'] = 'validate_experiment_execution'
            
            async for event in self._experiment_validation.run_async(ctx):
                yield event
            
            validation_status = ctx.session.state.get('validation_status', 'unknown')
            if validation_status != 'approved':
                print(f"❌ Experiment execution failed validation: {validation_status}")
                # May need to re-run experiments
        
        # --- Step 4: Results Extraction ---
        print("\n📊 Step 4: Results Extraction (Context-Aware)")
        print("-"*40)
        
        ctx.session.state['current_task'] = 'generate_results_extraction_plan'
        ctx.session.state['current_phase'] = 'results_extraction'
        
        # Orchestrator creates results extraction plan
        async for event in self._orchestrator_agent.run_async(ctx):
            yield event
        
        # Validate results extraction plan/code
        extraction_script = ctx.session.state.get('results_extraction_script_artifact')
        if extraction_script:
            ctx.session.state['artifact_to_validate'] = extraction_script
            ctx.session.state['current_task'] = 'validate_results_extraction'
            
            async for event in self._results_validation.run_async(ctx):
                yield event
            
            validation_status = ctx.session.state.get('validation_status', 'unknown')
            if validation_status != 'approved':
                print(f"⚠️  Results extraction needs refinement: {validation_status}")
        
        # Execute the results extraction
        print("\n🔄 Executing results extraction...")
        ctx.session.state['current_task'] = 'execute_results_extraction'
        
        # Run experiment executor to execute the extraction script
        async for event in self._experiment_executor.run_async(ctx):
            yield event
        
        # Final checkpoint
        results_artifact = ctx.session.state.get('final_results_artifact')
        checkpoint_manager.create_checkpoint(
            phase="implementation",
            step="complete",
            session_state=session_state or ctx.session.state,
            metadata={
                "results": results_artifact,
                "implementation_complete": True
            }
        )
        
        ctx.session.state['execution_status'] = 'complete'
        print("\n✅ Context-Aware Implementation Workflow Complete!")
        print(f"📊 Results: {results_artifact}")
        print("🔍 All phases validated with context-specific criteria")