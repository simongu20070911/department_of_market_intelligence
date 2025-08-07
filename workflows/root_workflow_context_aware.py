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
        from ..utils.micro_checkpoint_manager import micro_checkpoint_manager
        from datetime import datetime
        
        # Initialize workflow error handler
        error_handler = WorkflowErrorHandler(stop_on_critical=True)
        
        try:
            print("🚀 CONTEXT-AWARE ROOT WORKFLOW: Using Enhanced Phase Manager...")
            
            # Initialize simple state following ADK patterns
            task_id = ctx.session.state.get('domi_task_id', config.TASK_ID)
            
            # Initialize basic state if not present
            if 'domi_current_phase' not in ctx.session.state:
                ctx.session.state['domi_current_phase'] = WorkflowPhase.RESEARCH_PLANNING.value
            if 'domi_current_task' not in ctx.session.state:
                ctx.session.state['domi_current_task'] = "generate_initial_plan"
            if 'domi_task_id' not in ctx.session.state:
                ctx.session.state['domi_task_id'] = task_id
            if 'domi_current_date' not in ctx.session.state:
                ctx.session.state['domi_current_date'] = datetime.now().strftime("%Y-%m-%d")
            
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
                    
                    # Filter operations based on current phase
                    current_phase_str = ctx.session.state.get('domi_current_phase', 'research_planning')
                    current_phase_for_filter = WorkflowPhase.from_string(current_phase_str)
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
            
            # Handle phase mapping for execution -> implementation
            current_phase_str = ctx.session.state.get('domi_current_phase')
            current_phase = WorkflowPhase.from_string(current_phase_str)

            if current_phase and current_phase.name.startswith('EXPERIMENT'):
                print(f"⚠️ Detected '{current_phase.value}' phase from error checkpoint - rolling back to orchestration planning")
                ctx.session.state['domi_current_phase'] = WorkflowPhase.ORCHESTRATION_PLANNING.value
                # Reset to implementation planning state
                ctx.session.state['domi_current_task'] = 'orchestrate_implementation'
                ctx.session.state['domi_execution_status'] = 'pending'
                ctx.session.state['domi_validation_status'] = 'pending'
                
                # Set artifact to validate to implementation manifest for this phase
                dynamic_outputs_dir = config.get_outputs_dir(task_id)
                ctx.session.state['domi_artifact_to_validate'] = f"{dynamic_outputs_dir}/implementation/orchestration_plan.json"
                
                # Clear execution-specific state to start fresh
                if 'domi_coder_subtask' in ctx.session.state:
                    del ctx.session.state['domi_coder_subtask']
                if 'domi_implementation_manifest_artifact' in ctx.session.state:
                    # Keep the manifest but mark it as needing regeneration
                    ctx.session.state['domi_orchestrator_max_retries_reached'] = False
                    ctx.session.state['domi_orchestrator_iteration_count'] = 0
                
                # Clear failed execution micro-checkpoints
                if 'recoverable_ops' in locals() and recoverable_ops:
                    for op in recoverable_ops:
                        op_id = op.get('operation_id', '')
                        if 'execute_experiments' in op_id or 'orchestration' in op_id:
                            print(f"   🧹 Clearing failed operation: {op_id}")
                            try:
                                micro_checkpoint_manager.clear_operation(op_id)
                            except:
                                pass  # Ignore errors when clearing
            
            # --- Phase 1: Research Planning ---
            current_phase = WorkflowPhase.from_string(ctx.session.state.get('domi_current_phase'))
            if current_phase and current_phase.name.startswith('RESEARCH'):
                print("\n📊 PHASE 1: RESEARCH PLANNING (Context-Aware)")
                print("="*60)
                
                # Set up for research planning if not resuming
                if ctx.session.state.get('domi_current_phase') is None:
                    ctx.session.state['domi_current_phase'] = WorkflowPhase.RESEARCH_PLANNING.value
                    ctx.session.state['domi_current_task'] = "generate_initial_research_plan"
                    
                    # Set time context
                    current_date = datetime.now()
                    ctx.session.state['domi_current_date'] = current_date.strftime('%Y-%m-%d')
                    ctx.session.state['domi_current_datetime'] = current_date.strftime('%Y-%m-%d %H:%M:%S')
                    ctx.session.state['domi_current_year'] = str(current_date.year)
                    ctx.session.state['domi_current_month'] = str(current_date.month)
                
                # Set file paths
                if not ctx.session.state.get('domi_task_file_path'):
                    import os
                    ctx.session.state['domi_task_file_path'] = os.path.join(config.TASKS_DIR, f'{task_id}.md')
                
                # Create directory structure
                dynamic_outputs_dir = config.get_outputs_dir(task_id)
                ctx.session.state['domi_outputs_dir'] = dynamic_outputs_dir
                from ..utils.directory_manager import create_task_directory_structure, get_directory_structure_summary
                create_task_directory_structure(dynamic_outputs_dir)
                print(f"📁 Using task-specific outputs directory: {dynamic_outputs_dir}")
                print(f"   {get_directory_structure_summary(dynamic_outputs_dir)}")
                
                # Initialize validation
                ctx.session.state['domi_artifact_to_validate'] = f"{dynamic_outputs_dir}/planning/research_plan_v0.md"
                ctx.session.state['domi_validation_version'] = 0
                ctx.session.state['domi_validation_status'] = "pending"
                
                # Create checkpoint before planning
                checkpoint_manager.create_checkpoint(
                    phase=current_phase.value,
                    step="start",
                    session_state=ctx.session.state,
                    metadata={"workflow": "context_aware_root"}
                )
            
                # Run the planning workflow
                async for event in self._planning_workflow.run_async(ctx):
                    yield event
                
                # Check validation status after planning workflow completes
                validation_status = ctx.session.state.get('domi_validation_status', 'unknown')
                
                if validation_status == "approved":
                    print("✅ Research plan approved with context-aware validation!")
                    
                    # Transition to next phase BEFORE creating checkpoint
                    ctx.session.state['domi_current_phase'] = WorkflowPhase.ORCHESTRATION_PLANNING.value
                    # Reset validation status for the next phase to avoid using stale state
                    ctx.session.state['domi_validation_status'] = "pending"
                elif validation_status == "critical_error":
                    print("❌ Research plan validation resulted in critical error - halting workflow")
                    ctx.session.state['domi_execution_status'] = 'critical_error'
                    return  # Exit the workflow
                else:
                    print(f"❌ Research plan validation failed with status: {validation_status}")
                    print("⚠️  Workflow cannot proceed without an approved research plan")
                    ctx.session.state['domi_execution_status'] = 'validation_failed'
                    return  # Exit the workflow
                
                # Create checkpoint after planning (with updated phase)
                checkpoint_manager.create_checkpoint(
                    phase=WorkflowPhase.RESEARCH_PARALLEL_VALIDATION.value,
                    step="complete",
                    session_state=ctx.session.state,
                    metadata={"plan_version": ctx.session.state.get('domi_plan_version', 0)}
                )
            
            # --- Phase 2: Implementation with Retry Loop ---
            max_implementation_attempts = config.MAX_IMPLEMENTATION_ATTEMPTS
            implementation_attempt = 0
            
            current_phase = WorkflowPhase.from_string(ctx.session.state.get('domi_current_phase'))
            while current_phase and (current_phase.name.startswith('ORCHESTRATION') or current_phase.name.startswith('CODING')) and implementation_attempt < max_implementation_attempts:
                implementation_attempt += 1
                
                if implementation_attempt > 1:
                    print(f"\n🔄 PHASE 2: IMPLEMENTATION RETRY (Attempt {implementation_attempt}/{max_implementation_attempts})")
                    print("="*60)
                    print("🔄 Critical error detected - retrying implementation planning")
                    # Reset execution status for retry
                    ctx.session.state['domi_execution_status'] = 'pending'
                    ctx.session.state['domi_validation_status'] = 'pending'
                else:
                    print("\n🔧 PHASE 2: IMPLEMENTATION (Context-Aware)")
                    print("="*60)
                
                # Run the implementation workflow with context-aware validation
                async for event in self._implementation_workflow.run_async(ctx):
                    yield event
                
                # Check implementation status
                execution_status = ctx.session.state.get('domi_execution_status', 'unknown')
                
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
                    ctx.session.state['domi_current_phase'] = WorkflowPhase.FINAL_REPORT.value
                    # Reset validation status for the final report phase
                    ctx.session.state['domi_validation_status'] = "pending"
                    break
                else:
                    print(f"⚠️  Implementation ended with status: {execution_status}")
                    ctx.session.state['domi_current_phase'] = WorkflowPhase.FINAL_REPORT.value
                    break
                current_phase = WorkflowPhase.from_string(ctx.session.state.get('domi_current_phase'))

            
            if not (current_phase and (current_phase.name.startswith('ORCHESTRATION') or current_phase.name.startswith('CODING'))):
                print("\n🔧 SKIPPING PHASE 2: IMPLEMENTATION (already completed or not yet started)")
            
            # --- Phase 3: Final Report Generation ---
            current_phase = WorkflowPhase.from_string(ctx.session.state.get('domi_current_phase'))
            if current_phase == WorkflowPhase.FINAL_REPORT:
                print("\n📝 PHASE 3: FINAL REPORT GENERATION")
                print("="*60)
                
                ctx.session.state['domi_current_task'] = "generate_final_report"
                
                # Create checkpoint before final report
                checkpoint_manager.create_checkpoint(
                    phase=WorkflowPhase.FINAL_REPORT.value,
                    step="start",
                    session_state=ctx.session.state
                )
                
                # Run the chief researcher to generate final report
                async for event in self._chief_researcher.run_async(ctx):
                    yield event
            
            # Check the final execution status
            execution_status = ctx.session.state.get('domi_execution_status', 'unknown')
            current_phase_str = ctx.session.state.get('domi_current_phase', 'unknown')
            current_phase = WorkflowPhase.from_string(current_phase_str)

            # Only mark as complete if we successfully finished all phases
            if current_phase == WorkflowPhase.FINAL_REPORT and execution_status != 'critical_error':
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
                    phase=current_phase,
                    step="failed",
                    session_state=ctx.session.state,
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
            ctx.session.state['workflow_error'] = {
                'message': e.message,
                'level': e.level.value,
                'agent': e.agent_name,
                'timestamp': datetime.now().isoformat()
            }
            checkpoint_manager.create_checkpoint(
                phase="error",
                step=f"workflow_{e.level.value}",
                session_state=ctx.session.state
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
            ctx.session.state['workflow_error'] = {
                'message': str(e),
                'type': type(e).__name__,
                'timestamp': datetime.now().isoformat()
            }
            checkpoint_manager.create_checkpoint(
                phase="error",
                step="unexpected",
                session_state=ctx.session.state
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