# /department_of_market_intelligence/workflows/root_workflow_context_aware.py
"""Context-aware root workflow that uses intelligent validation."""

from typing import AsyncGenerator
from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event

from .research_planning_workflow_context_aware import (
    get_context_aware_research_planning_workflow,
    get_context_aware_orchestrator_workflow
)
from .implementation_workflow_context_aware import ImplementationWorkflowAgentContextAware
from ..agents.chief_researcher import get_chief_researcher_agent
from ..utils.state_adapter import StateAdapter
from .. import config


class RootWorkflowAgentContextAware(BaseAgent):
    """Context-aware master agent that orchestrates the entire research process."""

    def __init__(self, **kwargs):
        # Get context-aware sub-agents
        planning_workflow = get_context_aware_research_planning_workflow()
        implementation_workflow = ImplementationWorkflowAgentContextAware(name="ImplementationWorkflow")
        chief_researcher = get_chief_researcher_agent()
        
        # Store them as private attributes after initialization
        super().__init__(
            sub_agents=[
                planning_workflow,
                implementation_workflow,
                chief_researcher
            ],
            **kwargs
        )
        
        # Store references after parent initialization
        self._planning_workflow = planning_workflow
        self._implementation_workflow = implementation_workflow
        self._chief_researcher = chief_researcher

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        from ..utils.checkpoint_manager import checkpoint_manager
        from ..utils.state_model import SessionState
        from ..utils.state_adapter import StateAdapter
        from datetime import datetime
        
        # --- Initialize SessionState ---
        print("🚀 CONTEXT-AWARE ROOT WORKFLOW: Initializing SessionState...")
        
        # Get or create SessionState from existing dict state
        if hasattr(ctx.session, '_typed_state') and ctx.session._typed_state:
            # Use existing typed state
            session_state = ctx.session._typed_state
        else:
            # Create new SessionState from existing dict state
            task_id = ctx.session.state.get('task_id', 'research_session')
            
            if 'task_file_path' in ctx.session.state:
                # Convert existing dict state to SessionState
                session_state = StateAdapter.dict_to_session_state(ctx.session.state, task_id)
            else:
                # Create new SessionState
                session_state = SessionState(
                    task_id=task_id,
                    current_date=datetime.now().strftime("%Y-%m-%d")
                )
            
            # Store typed state on session object
            ctx.session._typed_state = session_state
        
        # Use StateProxy for state access
        from ..utils.state_adapter import StateProxy
        state_proxy = StateProxy(session_state)
        
        # Initialize checkpoint manager with task ID
        checkpoint_manager.task_id = session_state.task_id
        
        # --- Phase 1: Research Planning ---
        print("\n📊 PHASE 1: RESEARCH PLANNING (Context-Aware)")
        print("="*60)
        
        # Set up for research planning
        session_state.current_phase = "planning"
        session_state.current_task = "generate_initial_plan"
        
        # Set time context - required for agent templates
        from datetime import datetime
        current_date = datetime.now()
        session_state.metadata['current_date'] = current_date.strftime('%Y-%m-%d')
        session_state.metadata['current_datetime'] = current_date.strftime('%Y-%m-%d %H:%M:%S')
        session_state.metadata['current_year'] = str(current_date.year)
        session_state.metadata['current_month'] = str(current_date.month)
        
        # Set file paths - use absolute paths to prevent MCP path resolution issues
        if not session_state.task_file_path:
            import os
            session_state.task_file_path = os.path.join(config.TASKS_DIR, 'sample_research_task.md')
        session_state.metadata['outputs_dir'] = config.OUTPUTS_DIR
        
        # Initialize validation
        session_state.artifact_to_validate = f"{config.OUTPUTS_DIR}/research_plan_v0.md"
        session_state.validation_info.validation_version = 0
        
        # Replace session state for template access
        ctx.session.state = StateAdapter.create_proxy_state(session_state)
        
        # Create checkpoint before planning
        checkpoint_manager.create_checkpoint(
            phase="planning",
            step="start",
            session_state=session_state,
            metadata={"workflow": "context_aware_root"}
        )
        
        # Run the planning workflow
        async for event in self._planning_workflow.run_async(ctx):
            yield event
        
        print("✅ Research plan approved with context-aware validation!")
        
        # Create checkpoint after planning
        checkpoint_manager.create_checkpoint(
            phase="planning",
            step="complete",
            session_state=session_state,
            metadata={"plan_version": session_state.plan_version}
        )
        
        # --- Phase 2: Implementation ---
        print("\n🔧 PHASE 2: IMPLEMENTATION (Context-Aware)")
        print("="*60)
        
        session_state.current_phase = "implementation"
        
        # Run the implementation workflow with context-aware validation
        async for event in self._implementation_workflow.run_async(ctx):
            yield event
        
        # Check implementation status
        execution_status = state_proxy.get('execution_status', 'unknown')
        
        if execution_status == 'critical_error':
            print("❌ Critical error in implementation phase, stopping workflow")
            return
        elif execution_status != 'complete':
            print(f"⚠️  Implementation ended with status: {execution_status}")
        
        # --- Phase 3: Final Report Generation ---
        print("\n📝 PHASE 3: FINAL REPORT GENERATION")
        print("="*60)
        
        session_state.current_phase = "final_report"
        session_state.current_task = "generate_final_report"
        
        # Create checkpoint before final report
        checkpoint_manager.create_checkpoint(
            phase="final_report",
            step="start",
            session_state=session_state
        )
        
        # Run the chief researcher to generate final report
        async for event in self._chief_researcher.run_async(ctx):
            yield event
        
        # Final checkpoint
        final_report_path = state_proxy.get('final_report_artifact')
        checkpoint_manager.create_checkpoint(
            phase="final_report",
            step="complete",
            session_state=session_state,
            metadata={
                "final_report": final_report_path,
                "workflow_complete": True
            }
        )
        
        print("\n✅ CONTEXT-AWARE RESEARCH WORKFLOW COMPLETE!")
        print(f"📊 Final report: {final_report_path}")
        print(f"🔍 All validations performed with context awareness")


def get_context_aware_root_workflow():
    """Factory function to create context-aware root workflow."""
    return RootWorkflowAgentContextAware(name="ContextAwareRootWorkflow")