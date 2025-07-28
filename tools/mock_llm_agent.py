# /department_of_market_intelligence/tools/mock_llm_agent.py
"""Mock LLM agent for dry run mode - simulates agent behavior without API calls."""

import asyncio
from typing import AsyncGenerator
from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from .. import config

class MockLlmAgent(BaseAgent):
    """Mock LLM agent that simulates responses without making API calls."""
    
    def __init__(self, name: str, instruction: str = "", **kwargs):
        super().__init__(name=name, **kwargs)
        self._instruction = instruction  # Use private attribute to avoid Pydantic validation
        
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        print(f"[DRY RUN] Mock {self.name} agent would execute with instruction:")
        print(f"[DRY RUN] Session state keys: {list(ctx.session.state.keys())}")
        
        # Simulate different agent behaviors based on name
        if "Validator" in self.name:
            # Mock validation logic
            if "Junior" in self.name:
                ctx.session.state['junior_critique_artifact'] = f'outputs/junior_critique_v{ctx.session.state.get("validation_version", 0)}.md'
                print(f"[DRY RUN] {self.name} would write critique and set junior_critique_artifact")
            elif "Senior" in self.name:
                ctx.session.state['senior_critique_artifact'] = f'outputs/senior_critique_v{ctx.session.state.get("validation_version", 0)}.md'
                
                # Check if we're validating an executor failure
                current_execution_status = ctx.session.state.get('execution_status', '')
                if current_execution_status == 'critical_error':
                    ctx.session.state['validation_status'] = 'critical_error'  # Escalate for replanning
                    print(f"[DRY RUN] {self.name} detected critical error - validation_status='critical_error'")
                else:
                    ctx.session.state['validation_status'] = 'approved'  # Normal approval
                    print(f"[DRY RUN] {self.name} would approve with validation_status='approved'")
            elif "StatisticalValidator" in self.name:
                print(f"[DRY RUN] {self.name} would validate statistical rigor:")
                print(f"[DRY RUN]   - Sample size adequacy and power analysis")
                print(f"[DRY RUN]   - Hypothesis testing methodology")
                print(f"[DRY RUN]   - Multiple testing corrections")
                print(f"[DRY RUN]   - Risk-adjusted performance metrics")
                print(f"[DRY RUN] {self.name} found no critical statistical issues")
            elif "DataHygieneValidator" in self.name:
                print(f"[DRY RUN] {self.name} would validate data hygiene:")
                print(f"[DRY RUN]   - Data cleaning procedures")
                print(f"[DRY RUN]   - Missing data handling strategies")
                print(f"[DRY RUN]   - Outlier detection and treatment")
                print(f"[DRY RUN]   - Survivorship bias prevention")
                print(f"[DRY RUN] {self.name} found no critical data hygiene issues")
            elif "MethodologyValidator" in self.name:
                print(f"[DRY RUN] {self.name} would validate research methodology:")
                print(f"[DRY RUN]   - Experimental design validity")
                print(f"[DRY RUN]   - Factor model specification")
                print(f"[DRY RUN]   - Benchmark selection rationale")
                print(f"[DRY RUN]   - Transaction cost modeling")
                print(f"[DRY RUN] {self.name} found no critical methodology issues")
            elif "EfficiencyValidator" in self.name:
                print(f"[DRY RUN] {self.name} would validate efficiency and parallelization:")
                print(f"[DRY RUN]   - Checking for missed parallelization opportunities")
                print(f"[DRY RUN]   - Validating interface contracts and stitching points")
                print(f"[DRY RUN]   - Analyzing resource utilization")
                print(f"[DRY RUN]   - Identifying sequential bottlenecks")
                print(f"[DRY RUN] {self.name} found proper parallelization with clear stitching points")
            elif "GeneralValidator" in self.name:
                print(f"[DRY RUN] {self.name} would validate general aspects:")
                print(f"[DRY RUN]   - Logical consistency and flow")
                print(f"[DRY RUN]   - Completeness of analysis")
                print(f"[DRY RUN]   - Implementation feasibility")
                print(f"[DRY RUN]   - Timeline realism")
                print(f"[DRY RUN] {self.name} found no critical general issues")
                
        elif "Chief_Researcher" in self.name:
            # Mock chief researcher behavior
            current_task = ctx.session.state.get('current_task', '')
            if current_task == 'generate_initial_plan':
                ctx.session.state['plan_artifact_name'] = 'outputs/research_plan_v0.md'
                ctx.session.state['plan_version'] = 0
                print(f"[DRY RUN] {self.name} would generate initial plan")
            elif current_task == 'refine_plan':
                version = ctx.session.state.get('plan_version', 0) + 1
                ctx.session.state['plan_artifact_name'] = f'outputs/research_plan_v{version}.md'
                ctx.session.state['plan_version'] = version
                print(f"[DRY RUN] {self.name} would refine plan to version {version}")
                
        elif "Orchestrator" in self.name:
            # Check if we're replanning due to executor failure
            current_execution_status = ctx.session.state.get('execution_status', '')
            error_type = ctx.session.state.get('error_type', '')
            error_details = ctx.session.state.get('error_details', '')
            suggested_fix = ctx.session.state.get('suggested_fix', '')
            
            if current_execution_status == 'critical_error' and error_type:
                print(f"[DRY RUN] {self.name} REPLANNING with error context:")
                print(f"[DRY RUN]   - Error Type: {error_type}")
                print(f"[DRY RUN]   - Error Details: {error_details}")
                print(f"[DRY RUN]   - Suggested Fix: {suggested_fix}")
                print(f"[DRY RUN] {self.name} would UPDATE implementation plan with fixes")
                # Reset execution status since we're addressing the error
                ctx.session.state['execution_status'] = 'pending'
            else:
                print(f"[DRY RUN] {self.name} would create initial implementation plan")
            
            ctx.session.state['implementation_manifest_artifact'] = 'outputs/implementation_manifest.json'
            ctx.session.state['results_extraction_script_artifact'] = 'outputs/results_extraction.py'
            
        elif "Coder" in self.name:
            # Show task-specific information for parallel coding
            coder_subtask = ctx.session.state.get('coder_subtask', None)
            if coder_subtask:
                # Handle both dict and TaskInfo model
                if hasattr(coder_subtask, 'task_id'):
                    # It's a TaskInfo model
                    task_id = coder_subtask.task_id
                    description = coder_subtask.description
                    dependencies = coder_subtask.dependencies
                else:
                    # It's a dict (legacy format)
                    task_id = coder_subtask.get('task_id', 'unknown')
                    description = coder_subtask.get('description', 'no description')
                    dependencies = coder_subtask.get('dependencies', [])
                    
                print(f"[DRY RUN] {self.name} would generate code for:")
                print(f"[DRY RUN]   - Task: {task_id}")
                print(f"[DRY RUN]   - Description: {description}")
                print(f"[DRY RUN]   - Dependencies: {dependencies}")
            else:
                print(f"[DRY RUN] {self.name} would generate code")
            
        elif "Executor" in self.name:
            print(f"[DRY RUN] {self.name} would execute experiments")
            ctx.session.state['execution_status'] = 'success'  # Mock success
            
        # Simulate some processing time
        await asyncio.sleep(0.1)
        
        # Yield a simple completion event
        yield Event(
            author=self.name,
            actions=EventActions()
        )

def create_mock_llm_agent(name: str, instruction: str = "", **kwargs):
    """Factory function to create mock LLM agents."""
    return MockLlmAgent(name=name, instruction=instruction, **kwargs)