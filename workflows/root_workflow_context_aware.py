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
        # Initialize with no sub-agents; they will be created dynamically
        super().__init__(**kwargs)
        self._planning_workflow = None
        self._implementation_workflow = None
        self._chief_researcher = None

    def _initialize_workflows(self):
        """Initialize sub-workflows dynamically."""
        if self._planning_workflow is None:
            self._planning_workflow = get_context_aware_research_planning_workflow()
        if self._implementation_workflow is None:
            self._implementation_workflow = ImplementationWorkflowAgentContextAware(name="ImplementationWorkflow")
        if self._chief_researcher is None:
            self._chief_researcher = get_chief_researcher_agent()

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        # Initialize workflows here to ensure they have the correct context
        self._initialize_workflows()
        from ..utils.checkpoint_manager import checkpoint_manager
        from ..utils.micro_checkpoint_manager import micro_checkpoint_manager
        from datetime import datetime
        
        print("🚀 CONTEXT-AWARE ROOT WORKFLOW: Using simple ADK state management...")
        
        # Initialize simple state following ADK patterns
        task_id = ctx.session.state.get('task_id', config.TASK_ID)
        
        # Initialize basic state if not present
        if 'current_phase' not in ctx.session.state:
            ctx.session.state['current_phase'] = "planning"
        if 'current_task' not in ctx.session.state:
            ctx.session.state['current_task'] = "generate_initial_plan"
        if 'task_id' not in ctx.session.state:
            ctx.session.state['task_id'] = task_id
        if 'current_date' not in ctx.session.state:
            ctx.session.state['current_date'] = datetime.now().strftime("%Y-%m-%d")
        
        # Initialize checkpoint managers with task ID
        checkpoint_manager.task_id = task_id
        micro_checkpoint_manager.task_id = task_id
        
        # Initialize micro-checkpoints if enabled
        if config.ENABLE_MICRO_CHECKPOINTS:
            print("💾 Micro-checkpoints enabled for fine-grained recovery")
            
            # Check for recoverable operations
            recoverable_ops = micro_checkpoint_manager.list_recoverable_operations()
            if recoverable_ops:
                print(f"🔄 Found {len(recoverable_ops)} recoverable micro-operations")
                for op in recoverable_ops:
                    print(f"   • {op['operation_id']} ({op['agent_name']}): {op['progress']}")
                
                if config.MICRO_CHECKPOINT_AUTO_RESUME:
                    print("🔄 Auto-resuming micro-operations...")
                    # Note: Individual agents will handle their own operation resumption
        
        # --- Phase 1: Research Planning ---
        if ctx.session.state.get('current_phase') in [None, "planning"]:
            print("\n📊 PHASE 1: RESEARCH PLANNING (Context-Aware)")
            print("="*60)
            
            # Set up for research planning if not resuming
            if ctx.session.state.get('current_phase') is None:
                ctx.session.state['current_phase'] = "planning"
                ctx.session.state['current_task'] = "generate_initial_plan"
                
                # Set time context
                current_date = datetime.now()
                ctx.session.state['current_date'] = current_date.strftime('%Y-%m-%d')
                ctx.session.state['current_datetime'] = current_date.strftime('%Y-%m-%d %H:%M:%S')
                ctx.session.state['current_year'] = str(current_date.year)
                ctx.session.state['current_month'] = str(current_date.month)
                
                # Set file paths
                if not ctx.session.state.get('task_file_path'):
                    import os
                    ctx.session.state['task_file_path'] = os.path.join(config.TASKS_DIR, f'{task_id}.md')
                
                # Create directory structure
                dynamic_outputs_dir = config.get_outputs_dir(task_id)
                ctx.session.state['outputs_dir'] = dynamic_outputs_dir
                from ..utils.directory_manager import create_task_directory_structure, get_directory_structure_summary
                create_task_directory_structure(dynamic_outputs_dir)
                print(f"📁 Using task-specific outputs directory: {dynamic_outputs_dir}")
                print(f"   {get_directory_structure_summary(dynamic_outputs_dir)}")
                
                # Initialize validation
                ctx.session.state['artifact_to_validate'] = f"{dynamic_outputs_dir}/planning/research_plan_v0.md"
                ctx.session.state['validation_version'] = 0
                ctx.session.state['validation_status'] = "pending"
                
                # Create checkpoint before planning
                checkpoint_manager.create_checkpoint(
                    phase="planning",
                    step="start",
                    session_state=ctx.session.state,
                    metadata={"workflow": "context_aware_root"}
                )
            
            # Run the planning workflow
            async for event in self._planning_workflow.run_async(ctx):
                yield event
            
            print("✅ Research plan approved with context-aware validation!")
            
            # Transition to next phase BEFORE creating checkpoint
            ctx.session.state['current_phase'] = "implementation"
            # Reset validation status for the next phase to avoid using stale state
            ctx.session.state['validation_status'] = "pending"
            
            # Create checkpoint after planning (with updated phase)
            checkpoint_manager.create_checkpoint(
                phase="planning",
                step="complete",
                session_state=ctx.session.state,
                metadata={"plan_version": ctx.session.state.get('plan_version', 0)}
            )
        else:
            print("\n📊 SKIPPING PHASE 1: RESEARCH PLANNING (already completed)")
        
        # --- Phase 2: Implementation with Retry Loop ---
        max_implementation_attempts = config.MAX_IMPLEMENTATION_ATTEMPTS
        implementation_attempt = 0
        
        while ctx.session.state.get('current_phase') == "implementation" and implementation_attempt < max_implementation_attempts:
            implementation_attempt += 1
            
            if implementation_attempt > 1:
                print(f"\n🔄 PHASE 2: IMPLEMENTATION RETRY (Attempt {implementation_attempt}/{max_implementation_attempts})")
                print("="*60)
                print("🔄 Critical error detected - retrying implementation planning")
                # Reset execution status for retry
                ctx.session.state['execution_status'] = 'pending'
                ctx.session.state['validation_status'] = 'pending'
            else:
                print("\n🔧 PHASE 2: IMPLEMENTATION (Context-Aware)")
                print("="*60)
            
            # Run the implementation workflow with context-aware validation
            async for event in self._implementation_workflow.run_async(ctx):
                yield event
            
            # Check implementation status
            execution_status = ctx.session.state.get('execution_status', 'unknown')
            
            if execution_status == 'critical_error':
                if implementation_attempt < max_implementation_attempts:
                    print(f"❌ Implementation attempt {implementation_attempt} failed - preparing for retry")
                    # Stay in implementation phase for retry
                    continue
                else:
                    print("❌ Implementation failed after maximum attempts, stopping workflow")
                    return
            elif execution_status == 'complete':
                print("✅ Implementation completed successfully!")
                ctx.session.state['current_phase'] = "final_report"
                # Reset validation status for the final report phase
                ctx.session.state['validation_status'] = "pending"
                break
            else:
                print(f"⚠️  Implementation ended with status: {execution_status}")
                ctx.session.state['current_phase'] = "final_report"
                break
        
        if ctx.session.state.get('current_phase') != "implementation":
            print("\n🔧 SKIPPING PHASE 2: IMPLEMENTATION (already completed or not yet started)")
        
        # --- Phase 3: Final Report Generation ---
        if ctx.session.state.get('current_phase') == "final_report":
            print("\n📝 PHASE 3: FINAL REPORT GENERATION")
            print("="*60)
            
            ctx.session.state['current_task'] = "generate_final_report"
            
            # Create checkpoint before final report
            checkpoint_manager.create_checkpoint(
                phase="final_report",
                step="start",
                session_state=ctx.session.state
            )
            
            # Run the chief researcher to generate final report
            async for event in self._chief_researcher.run_async(ctx):
                yield event
        
        # Final checkpoint
        final_report_path = ctx.session.state.get('final_report_artifact')
        checkpoint_manager.create_checkpoint(
            phase="final_report",
            step="complete",
            session_state=ctx.session.state,
            metadata={
                "final_report": final_report_path,
                "workflow_complete": True,
                "micro_checkpoints_used": config.ENABLE_MICRO_CHECKPOINTS
            }
        )
        
        # Cleanup micro-checkpoints if enabled
        if config.ENABLE_MICRO_CHECKPOINTS:
            print("🧹 Cleaning up completed micro-operations...")
            micro_checkpoint_manager.cleanup_completed_operations(
                keep_days=config.MICRO_CHECKPOINT_CLEANUP_DAYS
            )
            
            # Show final micro-checkpoint summary
            recoverable_ops = micro_checkpoint_manager.list_recoverable_operations()
            if recoverable_ops:
                print(f"⚠️  {len(recoverable_ops)} micro-operations still recoverable")
            else:
                print("✅ All micro-operations completed successfully")
        
        print("\n✅ CONTEXT-AWARE RESEARCH WORKFLOW COMPLETE!")
        print(f"📊 Final report: {final_report_path}")
        print(f"🔍 All validations performed with context awareness")
        
        # Show comprehensive dry run summary if in dry run mode
        if config.DRY_RUN_MODE and config.DRY_RUN_COMPREHENSIVE_PATH_TESTING:
            from ..tools.mock_tools import get_dry_run_summary
            print("\n" + "="*80)
            print("🧪 COMPREHENSIVE DRY RUN TESTING SUMMARY")
            print("="*80)
            print(get_dry_run_summary())
            print("="*80)


def get_context_aware_root_workflow():
    """Factory function to create context-aware root workflow."""
    return RootWorkflowAgentContextAware(name="ContextAwareRootWorkflow")