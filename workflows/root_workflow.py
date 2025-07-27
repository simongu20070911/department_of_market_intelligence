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
        # --- Phase 1: Research Planning ---
        print("ROOT WORKFLOW: Starting Research Planning Phase...")
        ctx.session.state['current_task'] = 'generate_initial_plan'
        ctx.session.state['validation_version'] = 0  # Initialize validation version
        ctx.session.state['artifact_to_validate'] = 'outputs/research_plan_v0.md'  # Initial artifact to validate
        async for event in self._planning_workflow.run_async(ctx):
            yield event
        print("ROOT WORKFLOW: Research Plan Approved.")

        # --- Phase 2: Implementation & Execution ---
        max_attempts = 3 # Failsafe for the execution feedback loop
        for attempt in range(max_attempts):
            print(f"ROOT WORKFLOW: Starting Implementation & Execution Phase (Attempt {attempt + 1}/{max_attempts})...")
            ctx.session.state['current_task'] = 'generate_implementation_plan'
            # Reset execution status for the new attempt
            ctx.session.state['execution_status'] = 'pending'

            async for event in self._implementation_workflow.run_async(ctx):
                yield event
            
            # Check for critical errors signaled by the Executor
            if ctx.session.state.get('execution_status') != 'critical_error':
                print("ROOT WORKFLOW: Execution Phase Completed Successfully.")
                break # Exit the loop if successful
            else:
                print("ROOT WORKFLOW: Critical error detected in execution. Looping back to implementation planning.")
                # The loop will naturally restart, and the orchestrator/coders will have
                # access to the error report artifact to inform their next attempt.
        else: # This 'else' belongs to the 'for' loop, it runs if the loop completes without a 'break'
            print("ROOT WORKFLOW: Maximum execution attempts reached. Aborting.")
            # You could yield a final error event here
            return

        # --- Phase 3: Final Reporting ---
        print("ROOT WORKFLOW: Starting Final Reporting Phase...")
        ctx.session.state['current_task'] = 'generate_final_report'
        async for event in self._chief_researcher.run_async(ctx):
            yield event
        
        print("ROOT WORKFLOW: Process Complete.")