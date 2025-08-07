# /department_of_market_intelligence/workflows/root_workflow_context_aware.py
"""Context-aware root workflow that uses intelligent validation."""

from typing import AsyncGenerator
from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event

from .research_planning_workflow_context_aware import (
    get_context_aware_research_planning_workflow
)
from .implementation_workflow_context_aware import ImplementationWorkflowAgentContextAware
from ..agents.chief_researcher import get_chief_researcher_agent
from ..utils.state_adapter import get_domi_state
from ..utils.workflow_errors import WorkflowError, WorkflowErrorHandler
from ..utils.phase_manager import WorkflowPhase, enhanced_phase_manager
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
        from datetime import datetime
        
        # Initialize workflow error handler
        error_handler = WorkflowErrorHandler(stop_on_critical=True)
        
        try:
            print("🚀 CONTEXT-AWARE ROOT WORKFLOW: Using Enhanced Phase Manager...")
            
            # Get structured state
            domi_state = get_domi_state(ctx)

            # Initialize checkpoint managers with task ID
            checkpoint_manager.task_id = domi_state.task_id
            
            # Initialize micro-checkpoints if enabled
            if config.ENABLE_MICRO_CHECKPOINTS:
                print("💾 Micro-checkpoints enabled for fine-grained recovery")
                
                # Check for recoverable operations
                recoverable_ops = checkpoint_manager.list_recoverable_operations()
                if recoverable_ops:
                    print(f"🔄 Found {len(recoverable_ops)} recoverable micro-operations")
                    
                    # Filter operations based on current phase
                    current_phase_for_filter = WorkflowPhase.from_string(domi_state.current_phase)
                    phase_appropriate_ops = []
                    
                    for op in recoverable_ops:
                        op_id = op.get('operation_id', '')
                        agent_name = op.get('agent_name', '')
                        
                        # Skip planning operations if not in a research phase
                        if 'research' in op_id.lower() and not current_phase_for_filter.name.startswith('RESEARCH'):
                            print(f"   ⏭️  Skipping {op_id} ({agent_name}) - not in a research phase")
                            continue
                        
                        # Skip orchestration operations if not in an orchestration phase
                        if 'orchestration' in op_id.lower() and not current_phase_for_filter.name.startswith('ORCHESTRATION'):
                            print(f"   ⏭️  Skipping {op_id} ({agent_name}) - not in an orchestration phase")
                            continue
                            
                        phase_appropriate_ops.append(op)
                        print(f"   • {op_id} ({agent_name}): {op['progress']}")
                    
                    if config.MICRO_CHECKPOINT_AUTO_RESUME and phase_appropriate_ops:
                        print(f"🔄 Auto-resuming {len(phase_appropriate_ops)} phase-appropriate micro-operations...")
                        # Note: Individual agents will handle their own operation resumption
            
            # --- Phase 1: Research Planning ---
            current_phase = WorkflowPhase.from_string(domi_state.current_phase)
            if current_phase and enhanced_phase_manager.get_phase_config(current_phase).primary_agent == "Chief_Researcher":
                print(f"\n📊 Executing {current_phase.value}...")
                # ... (setup code)

                # Run the planning workflow
                async for event in self._planning_workflow.run_async(ctx):
                    yield event

                # ... (phase transition logic)
            
            # --- Phase 2: Implementation with Retry Loop ---
            max_implementation_attempts = config.MAX_IMPLEMENTATION_ATTEMPTS
            implementation_attempt = 0
            
            current_phase = WorkflowPhase.from_string(domi_state.current_phase)
            implementation_phases = {
                phase for phase_group in [
                    'orchestration', 'coding', 'experiment', 'results'
                ] for phase in enhanced_phase_manager.get_validation_loop_phases().get(phase_group, [])
            }
            while current_phase and current_phase in implementation_phases and implementation_attempt < max_implementation_attempts:
                implementation_attempt += 1
                
                if implementation_attempt > 1:
                    print(f"\n🔄 PHASE 2: IMPLEMENTATION RETRY (Attempt {implementation_attempt}/{max_implementation_attempts})")
                    print("="*60)
                    print("🔄 Critical error detected - retrying implementation planning")
                    # Reset execution status for retry
                    domi_state.execution.execution_status = 'pending'
                    domi_state.validation.validation_status = 'pending'
                else:
                    print("\n🔧 PHASE 2: IMPLEMENTATION (Context-Aware)")
                    print("="*60)
                
                # Run the implementation workflow with context-aware validation
                async for event in self._implementation_workflow.run_async(ctx):
                    yield event
                
                # Check implementation status
                execution_status = domi_state.execution.execution_status
                
                if execution_status == 'critical_error':
                    if implementation_attempt < max_implementation_attempts:
                        print(f"❌ Implementation attempt {implementation_attempt} failed - preparing for retry")
                        rollback_phase = enhanced_phase_manager.get_rollback_target(current_phase)
                        domi_state.current_phase = rollback_phase.value
                        continue
                    else:
                        print("❌ Implementation failed after maximum attempts, stopping workflow")
                        return
                elif execution_status == 'completed':
                    print("✅ Implementation completed successfully!")
                    next_phase = enhanced_phase_manager.get_phase_config(current_phase).next_phases[0]
                    domi_state.current_phase = next_phase.value
                    domi_state.validation.validation_status = "pending"
                    break
                else:
                    print(f"⚠️  Implementation ended with status: {execution_status}")
                    next_phase = enhanced_phase_manager.get_phase_config(current_phase).next_phases[0]
                    domi_state.current_phase = next_phase.value
                    break
                current_phase = WorkflowPhase.from_string(domi_state.current_phase)

            
            if not (current_phase and current_phase in implementation_phases):
                print("\n🔧 SKIPPING PHASE 2: IMPLEMENTATION (already completed or not yet started)")
            
            # --- Phase 3: Final Report Generation ---
            current_phase = WorkflowPhase.from_string(domi_state.current_phase)
            if current_phase and enhanced_phase_manager.get_phase_config(current_phase).primary_agent == "Chief_Researcher" and not current_phase.name.startswith('RESEARCH'):
                print("\n📝 PHASE 3: FINAL REPORT GENERATION")
                print("="*60)
                
                domi_state.current_task_description = "generate_final_report"
                
                # Create checkpoint before final report
                checkpoint_manager.create_checkpoint(
                    phase=WorkflowPhase.FINAL_REPORT.value,
                    step="start",
                    session_state=domi_state.to_checkpoint_dict()
                )
                
                # Run the chief researcher to generate final report
                async for event in self._chief_researcher.run_async(ctx):
                    yield event
            
            # Check the final execution status
            execution_status = domi_state.execution.execution_status
            current_phase = WorkflowPhase.from_string(domi_state.current_phase)

            # Only mark as complete if we successfully finished all phases
            if current_phase == WorkflowPhase.FINAL_REPORT and execution_status != 'critical_error':
                # Final checkpoint
                final_report_path = domi_state.execution.final_report_artifact
                checkpoint_manager.create_checkpoint(
                    phase="final_report",
                    step="complete",
                    session_state=domi_state.to_checkpoint_dict(),
                    metadata={
                        "final_report": final_report_path,
                        "workflow_complete": True,
                        "micro_checkpoints_used": config.ENABLE_MICRO_CHECKPOINTS
                    }
                )
                
                # Cleanup micro-checkpoints if enabled
                if config.ENABLE_MICRO_CHECKPOINTS:
                    print("🧹 Cleaning up completed micro-operations...")
                    checkpoint_manager.cleanup_completed_operations(
                        keep_days=config.MICRO_CHECKPOINT_CLEANUP_DAYS
                    )
                    
                    # Show final micro-checkpoint summary
                    recoverable_ops = checkpoint_manager.list_recoverable_operations()
                    if recoverable_ops:
                        print(f"⚠️  {len(recoverable_ops)} micro-operations still recoverable")
                    else:
                        print("✅ All micro-operations completed successfully")
                
                print("\n✅ CONTEXT-AWARE RESEARCH WORKFLOW COMPLETE!")
                print(f"📊 Final report: {final_report_path}")
                print(f"🔍 All validations performed with context awareness")
            else:
                # Workflow did not complete successfully
                print("\n❌ CONTEXT-AWARE RESEARCH WORKFLOW FAILED TO COMPLETE")
                print(f"📊 Final phase reached: {current_phase}")
                print(f"📊 Execution status: {execution_status}")
            
                if execution_status == 'critical_error':
                    print("⚠️  Workflow halted due to critical validation error")
                elif execution_status == 'validation_failed':
                    print("⚠️  Workflow halted due to validation failure")
                else:
                    print("⚠️  Workflow ended prematurely")
                    
                # Save failure checkpoint for debugging
                checkpoint_manager.create_checkpoint(
                    phase=current_phase.value,
                    step="failed",
                    session_state=domi_state.to_checkpoint_dict(),
                    metadata={
                        "workflow_complete": False,
                        "failure_reason": execution_status,
                        "micro_checkpoints_used": config.ENABLE_MICRO_CHECKPOINTS
                    }
                )
            
            # Show comprehensive dry run summary if in dry run mode
            if config.DRY_RUN_MODE and config.DRY_RUN_COMPREHENSIVE_PATH_TESTING:
                from ..tools.mock_tools import get_dry_run_summary
                print("\n" + "="*80)
                print("🧪 COMPREHENSIVE DRY RUN TESTING SUMMARY")
                print("="*80)
                print(get_dry_run_summary())
                print("="*80)
                
        except WorkflowError as e:
            # Handle workflow errors
            print(f"\n{'='*80}")
            print(f"🚨 WORKFLOW TERMINATED DUE TO CRITICAL ERROR")
            print(f"{'='*80}")
            print(f"Error: {e.message}")
            print(f"Level: {e.level.value.upper()}")
            print(f"Agent: {e.agent_name or 'Unknown'}")
            print(f"{'='*80}\n")
            
            # Save error state to checkpoint
            domi_state.metadata['workflow_error'] = {
                'message': e.message,
                'level': e.level.value,
                'agent': e.agent_name,
                'timestamp': datetime.now().isoformat()
            }
            checkpoint_manager.create_checkpoint(
                phase="error",
                step=f"workflow_{e.level.value}",
                session_state=domi_state.to_checkpoint_dict()
            )
            
            # Re-raise to stop the workflow completely
            raise
            
        except Exception as e:
            # Handle unexpected errors
            print(f"\n{'='*80}")
            print(f"💀 UNEXPECTED ERROR IN WORKFLOW")
            print(f"{'='*80}")
            print(f"Error: {str(e)}")
            print(f"Type: {type(e).__name__}")
            print(f"{'='*80}\n")
            
            # Save error state
            domi_state.metadata['workflow_error'] = {
                'message': str(e),
                'type': type(e).__name__,
                'timestamp': datetime.now().isoformat()
            }
            checkpoint_manager.create_checkpoint(
                phase="error",
                step="unexpected",
                session_state=domi_state.to_checkpoint_dict()
            )
            
            # Re-raise
            raise
            
        finally:
            # Always print error summary if there were any issues
            if error_handler.errors or error_handler.warnings:
                print("\n" + "="*60)
                print("📋 WORKFLOW ERROR SUMMARY")
                print("="*60)
                print(error_handler.get_summary())
                print("="*60)


def get_context_aware_root_workflow():
    """Factory function to create context-aware root workflow."""
    return RootWorkflowAgentContextAware(name="ContextAwareRootWorkflow")