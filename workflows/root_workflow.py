# /department_of_market_intelligence/workflows/root_workflow.py
from typing import AsyncGenerator
from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from .research_planning_workflow import get_research_planning_workflow
from .implementation_workflow import ImplementationWorkflowAgent
from ..agents.chief_researcher import get_chief_researcher_agent

class RootWorkflowAgent(BaseAgent):
    """The master agent that orchestrates the entire research process."""

    def __init__(self, **kwargs):
        # Get the sub-agents
        planning_workflow = get_research_planning_workflow()
        implementation_workflow = ImplementationWorkflowAgent(name="ImplementationWorkflow")
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
        from .. import config
        from datetime import datetime
        
        # --- Initialize SessionState ---
        print("ROOT WORKFLOW: Initializing SessionState...")
        
        # Get or create SessionState from existing dict state
        if hasattr(ctx.session, '_typed_state') and ctx.session._typed_state:
            # Use existing typed state
            session_state = ctx.session._typed_state
        else:
            # Create new SessionState from existing dict state
            task_id = ctx.session.state.get('task_id', 'research_session')
            session_state = StateAdapter.dict_to_session_state(dict(ctx.session.state), task_id)
            
            # Initialize required fields
            session_state.current_phase = "planning"
            session_state.current_task = "generate_initial_plan"
            
            # Set time context
            current_date = datetime.now()
            session_state.metadata['current_date'] = current_date.strftime('%Y-%m-%d')
            session_state.metadata['current_datetime'] = current_date.strftime('%Y-%m-%d %H:%M:%S')
            session_state.metadata['current_year'] = str(current_date.year)
            session_state.metadata['current_month'] = str(current_date.month)
            
            # Set file paths
            if not session_state.task_file_path:
                session_state.task_file_path = 'tasks/sample_research_task.md'
            session_state.metadata['outputs_dir'] = config.OUTPUTS_DIR
            
            # Initialize validation
            session_state.artifact_to_validate = f"{config.OUTPUTS_DIR}/research_plan_v0.md"
            session_state.validation_info.validation_version = 0
            
            # Create proxy for backward compatibility
            ctx.session._typed_state = session_state
            ctx.session.state = StateAdapter.create_proxy_state(session_state)
        
        # --- Phase 1: Research Planning ---
        print("ROOT WORKFLOW: Starting Research Planning Phase...")
        
        # Create initial checkpoint using SessionState
        checkpoint_manager.create_checkpoint(
            phase="research_planning",
            step="phase_start",
            session_state=session_state.to_checkpoint_dict(),
            metadata={"phase_description": "Beginning research planning phase"}
        )
        
        if config.DRY_RUN_MODE:
            print("*** DRY RUN MODE ENABLED ***")
            print(f"- Max iterations limited to {config.MAX_DRY_RUN_ITERATIONS}")
            print("- This mode validates workflows without full execution")
        async for event in self._planning_workflow.run_async(ctx):
            yield event
        print("ROOT WORKFLOW: Research Plan Approved.")
        
        # Checkpoint after planning phase completion
        checkpoint_manager.create_checkpoint(
            phase="research_planning",
            step="phase_complete",
            session_state=dict(ctx.session.state),
            metadata={"phase_description": "Research planning completed and approved"}
        )

        # --- Phase 2: Implementation & Execution ---
        max_attempts = 3 # Failsafe for the execution feedback loop
        for attempt in range(max_attempts):
            print(f"ROOT WORKFLOW: Starting Implementation & Execution Phase (Attempt {attempt + 1}/{max_attempts})...")
            
            # Checkpoint before each implementation attempt
            checkpoint_manager.create_checkpoint(
                phase="implementation_execution",
                step=f"attempt_{attempt + 1}_start",
                session_state=dict(ctx.session.state),
                metadata={
                    "attempt_number": attempt + 1,
                    "max_attempts": max_attempts,
                    "phase_description": f"Starting implementation attempt {attempt + 1}"
                }
            )
            
            ctx.session.state['current_task'] = 'generate_implementation_plan'
            # Reset execution status for the new attempt
            ctx.session.state['execution_status'] = 'pending'

            async for event in self._implementation_workflow.run_async(ctx):
                yield event
            
            # Check for critical errors signaled by the Executor
            if ctx.session.state.get('execution_status') != 'critical_error':
                print("ROOT WORKFLOW: Execution Phase Completed Successfully.")
                
                # Checkpoint successful execution
                checkpoint_manager.create_checkpoint(
                    phase="implementation_execution",
                    step="phase_complete",
                    session_state=dict(ctx.session.state),
                    metadata={
                        "attempt_number": attempt + 1,
                        "success": True,
                        "phase_description": "Implementation and execution completed successfully"
                    }
                )
                break # Exit the loop if successful
            else:
                print("ROOT WORKFLOW: Critical error detected in execution. Looping back to implementation planning.")
                
                # Checkpoint failed execution for recovery
                checkpoint_manager.create_checkpoint(
                    phase="implementation_execution",
                    step=f"attempt_{attempt + 1}_failed",
                    session_state=dict(ctx.session.state),
                    metadata={
                        "attempt_number": attempt + 1,
                        "success": False,
                        "error_type": ctx.session.state.get('error_type', 'unknown'),
                        "error_details": ctx.session.state.get('error_details', 'unknown'),
                        "phase_description": f"Implementation attempt {attempt + 1} failed"
                    }
                )
                # The loop will naturally restart, and the orchestrator/coders will have
                # access to the error report artifact to inform their next attempt.
        else: # This 'else' belongs to the 'for' loop, it runs if the loop completes without a 'break'
            print("ROOT WORKFLOW: Maximum execution attempts reached. Aborting.")
            # You could yield a final error event here
            return

        # --- Phase 3: Final Reporting ---
        print("ROOT WORKFLOW: Starting Final Reporting Phase...")
        
        # Checkpoint before final reporting
        checkpoint_manager.create_checkpoint(
            phase="final_reporting",
            step="phase_start",
            session_state=dict(ctx.session.state),
            metadata={"phase_description": "Starting final report generation"}
        )
        
        ctx.session.state['current_task'] = 'generate_final_report'
        async for event in self._chief_researcher.run_async(ctx):
            yield event
        
        print("ROOT WORKFLOW: Process Complete.")
        
        # Final checkpoint - task completion
        checkpoint_manager.create_checkpoint(
            phase="final_reporting",
            step="task_complete",
            session_state=dict(ctx.session.state),
            metadata={
                "phase_description": "Research task completed successfully",
                "task_status": "completed",
                "total_agent_executions": checkpoint_manager.agent_execution_count
            }
        )
        
        # Cleanup old checkpoints but keep some for recovery
        checkpoint_manager.cleanup_old_checkpoints(keep_count=5)


def get_root_workflow():
    """Get the root workflow agent."""
    return RootWorkflowAgent(name="RootWorkflow")