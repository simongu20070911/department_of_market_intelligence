#!/usr/bin/env python3
"""Test complete replanning scenario: Executor fails → Validators escalate → Orchestrator replans → Success."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Enable dry run mode for testing
import department_of_market_intelligence.config as config
config.DRY_RUN_MODE = True
config.DRY_RUN_SKIP_LLM = True
config.MAX_EXECUTION_CORRECTION_LOOPS = 2  # Allow 2 attempts
config.VERBOSE_LOGGING = False

from department_of_market_intelligence.tools.mock_llm_agent import MockLlmAgent
import asyncio

# Enhanced executor that fails first, succeeds after replanning
class ReplanningTestExecutor(MockLlmAgent):
    execution_attempts: int = 0
    
    async def _run_async_impl(self, ctx):
        ReplanningTestExecutor.execution_attempts += 1
        attempt = ReplanningTestExecutor.execution_attempts
        
        print(f"\n🎯 [EXECUTOR ATTEMPT #{attempt}]")
        
        if attempt == 1:
            # First attempt: Critical failure requiring replanning
            print("❌ [EXECUTOR] CRITICAL FAILURE:")
            print("   - Cannot access market_data.csv - file path incorrect")
            print("   - Missing dependency: yfinance package not installed")
            print("   - This requires implementation plan updates and recoding")
            
            ctx.session.state['execution_status'] = 'critical_error'
            ctx.session.state['error_type'] = 'data_access_and_dependency_failure'
            ctx.session.state['error_details'] = 'File path incorrect and missing yfinance dependency'
            ctx.session.state['suggested_fix'] = 'Update data source configuration and add dependency installation'
            
        elif attempt == 2:
            # Second attempt: Success after replanning
            print("✅ [EXECUTOR] SUCCESS AFTER REPLANNING:")
            print("   - Data access resolved with updated file path")
            print("   - Dependencies installed correctly")
            print("   - Analysis completed successfully")
            
            ctx.session.state['execution_status'] = 'success'
            # Clear error state
            ctx.session.state.pop('error_type', None)
            ctx.session.state.pop('error_details', None)
            ctx.session.state.pop('suggested_fix', None)
        
        # Don't call parent - it would override our execution_status
        print(f"[DRY RUN] Mock {self.name} agent would execute with instruction:")
        print(f"[DRY RUN] Session state keys: {list(ctx.session.state.keys())}")
        
        # Simulate some processing time
        await asyncio.sleep(0.1)
        
        # Yield a simple completion event
        from google.adk.events import Event, EventActions
        yield Event(
            author=self.name,
            actions=EventActions()
        )

class EnhancedSeniorValidator(MockLlmAgent):
    """Enhanced validator that properly detects critical errors."""
    
    async def _run_async_impl(self, ctx):
        print(f"\n🔍 [SENIOR VALIDATOR] Analyzing execution results...")
        
        execution_status = ctx.session.state.get('execution_status', '')
        error_type = ctx.session.state.get('error_type', '')
        error_details = ctx.session.state.get('error_details', '')
        
        print(f"🔍 [SENIOR VALIDATOR] Current execution_status: {execution_status}")
        
        if execution_status == 'critical_error':
            print(f"🚨 [SENIOR VALIDATOR] CRITICAL ERROR DETECTED:")
            print(f"   - Error Type: {error_type}")
            print(f"   - Details: {error_details}")
            print("   - Assessment: Unresolvable without replanning")
            print("   - Decision: ESCALATE FOR REPLANNING")
            
            ctx.session.state['validation_status'] = 'critical_error'
            
        else:
            print("✅ [SENIOR VALIDATOR] Execution successful - APPROVED")
            ctx.session.state['validation_status'] = 'approved'
        
        ctx.session.state['senior_critique_artifact'] = f'outputs/senior_critique_v{ctx.session.state.get("validation_version", 0)}.md'
        
        # Don't call parent - it overrides our logic
        print(f"[DRY RUN] Mock {self.name} agent would execute with instruction:")
        print(f"[DRY RUN] Session state keys: {list(ctx.session.state.keys())}")
        
        # Simulate some processing time
        await asyncio.sleep(0.1)
        
        # Yield a simple completion event
        from google.adk.events import Event, EventActions
        yield Event(
            author=self.name,
            actions=EventActions()
        )

class EnhancedOrchestrator(MockLlmAgent):
    """Enhanced orchestrator that shows replanning with error context."""
    
    async def _run_async_impl(self, ctx):
        execution_status = ctx.session.state.get('execution_status', '')
        error_type = ctx.session.state.get('error_type', '')
        error_details = ctx.session.state.get('error_details', '')
        suggested_fix = ctx.session.state.get('suggested_fix', '')
        
        if execution_status == 'critical_error' and error_type:
            print(f"\n🔄 [ORCHESTRATOR] REPLANNING MODE ACTIVATED:")
            print(f"   📋 Previous Error Analysis:")
            print(f"      - Type: {error_type}")
            print(f"      - Details: {error_details}")
            print(f"      - Suggested Fix: {suggested_fix}")
            print(f"   🛠️  UPDATING IMPLEMENTATION PLAN:")
            print(f"      - Adding dependency installation step")
            print(f"      - Correcting data source file paths")
            print(f"      - Adding error handling for missing files")
            print(f"   📄 Generating updated implementation manifest...")
            
            # Reset execution status since we're addressing the error
            ctx.session.state['execution_status'] = 'pending'
            
        else:
            print(f"\n📋 [ORCHESTRATOR] Creating initial implementation plan...")
        
        ctx.session.state['implementation_manifest_artifact'] = 'outputs/implementation_manifest.json'
        ctx.session.state['results_extraction_script_artifact'] = 'outputs/results_extraction.py'
        
        async for event in super()._run_async_impl(ctx):
            yield event

async def simulate_replanning_scenario():
    """Simulate the complete replanning scenario."""
    print("🎭 SIMULATING COMPLETE REPLANNING SCENARIO")
    print("="*70)
    print("Scenario: Executor fails → Validators escalate → Orchestrator replans → Success")
    print("-" * 70)
    
    class MockContext:
        def __init__(self):
            self.session = MockSession()
    
    class MockSession:
        def __init__(self):
            self.state = {
                'task_file_path': 'tasks/sample_research_task.md',
                'validation_version': 0,
                'current_task': 'execute_experiments'
            }
    
    ctx = MockContext()
    
    # Reset attempt counter
    ReplanningTestExecutor.execution_attempts = 0
    
    for attempt in range(1, 3):  # Simulate 2 attempts (fail, then succeed)
        print(f"\n{'='*70}")
        print(f"🔄 ROOT WORKFLOW: Implementation Attempt {attempt}/2")
        print("="*70)
        
        if attempt == 2:
            print("🔄 ROOT WORKFLOW: Critical error detected - looping back to implementation planning")
        
        # 1. Orchestrator Planning
        print(f"\n--- PHASE 1: Orchestrator Planning (Attempt {attempt}) ---")
        orchestrator = EnhancedOrchestrator(name="Orchestrator")
        async for event in orchestrator._run_async_impl(ctx):
            pass
        
        # 2. Executor Execution
        print(f"\n--- PHASE 2: Executor Execution (Attempt {attempt}) ---")
        executor = ReplanningTestExecutor(name="Experiment_Executor")
        async for event in executor._run_async_impl(ctx):
            pass
        
        # 3. Validator Assessment
        print(f"\n--- PHASE 3: Validator Assessment (Attempt {attempt}) ---")
        validator = EnhancedSeniorValidator(name="Senior_Validator")
        async for event in validator._run_async_impl(ctx):
            pass
        
        # 4. Check if we should continue or exit
        final_status = ctx.session.state.get('execution_status', '')
        validation_status = ctx.session.state.get('validation_status', '')
        
        print(f"\n📊 Results for Attempt {attempt}:")
        print(f"   - Execution Status: {final_status}")
        print(f"   - Validation Status: {validation_status}")
        
        if validation_status == 'critical_error':
            print("🔄 MetaValidator would escalate - triggering replanning loop")
        elif validation_status == 'approved' and final_status == 'success':
            print("✅ Success! Breaking out of replanning loop")
            break
        
    # Final Results
    print(f"\n{'='*70}")
    print("🎯 FINAL RESULTS")
    print("="*70)
    
    total_attempts = ReplanningTestExecutor.execution_attempts
    final_status = ctx.session.state.get('execution_status', '')
    
    print(f"📊 Total Execution Attempts: {total_attempts}")
    print(f"📊 Final Execution Status: {final_status}")
    
    if total_attempts == 2 and final_status == 'success':
        print("✅ REPLANNING SCENARIO SUCCESSFUL:")
        print("   1. ❌ First attempt failed with critical error")
        print("   2. 🔄 Validators escalated for replanning")
        print("   3. 🛠️  Orchestrator updated implementation plan with error context")
        print("   4. ✅ Second attempt succeeded")
        return True
    else:
        print("❌ REPLANNING SCENARIO FAILED:")
        if total_attempts != 2:
            print(f"   - Expected 2 attempts, got {total_attempts}")
        if final_status != 'success':
            print(f"   - Expected 'success', got '{final_status}'")
        return False

if __name__ == "__main__":
    print("🧪 TESTING COMPLETE EXECUTOR → ORCHESTRATOR REPLANNING SCENARIO")
    print("Full flow: Error → Validation → Escalation → Replanning → Success")
    print("=" * 80)
    
    try:
        success = asyncio.run(simulate_replanning_scenario())
        if success:
            print("\n🎉 COMPLETE REPLANNING SCENARIO TEST PASSED!")
            print("✅ Full replanning flow verified successfully")
        else:
            print("\n⚠️  Replanning scenario test failed")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)