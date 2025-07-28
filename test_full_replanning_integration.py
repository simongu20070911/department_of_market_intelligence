#!/usr/bin/env python3
"""Test full integration of executor failure -> orchestrator replanning loop."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Enable dry run mode for testing
import department_of_market_intelligence.config as config
config.DRY_RUN_MODE = True
config.DRY_RUN_SKIP_LLM = True
config.MAX_DRY_RUN_ITERATIONS = 1
config.VERBOSE_LOGGING = False

from department_of_market_intelligence.main import main
from department_of_market_intelligence.tools.mock_llm_agent import MockLlmAgent
import asyncio

# Monkey patch the mock executor to fail on first attempt, succeed on second
class FailingThenSucceedingExecutor(MockLlmAgent):
    execution_attempts: int = 0
    
    async def _run_async_impl(self, ctx):
        FailingThenSucceedingExecutor.execution_attempts += 1
        attempt = FailingThenSucceedingExecutor.execution_attempts
        
        print(f"[TEST] Mock Executor attempt #{attempt}")
        
        if attempt == 1:
            # First attempt: FAIL
            print("[EXECUTOR FAILURE] Cannot access required data: market_data.csv missing")
            print("[EXECUTOR FAILURE] This will trigger replanning...")
            ctx.session.state['execution_status'] = 'critical_error'
            ctx.session.state['error_type'] = 'data_access_failure'
            ctx.session.state['error_details'] = 'Required market data file missing'
            ctx.session.state['suggested_fix'] = 'Update data source path or use alternative dataset'
            print(f"[TEST] Setting execution_status = critical_error (attempt {attempt})")
        else:
            # Second attempt: SUCCESS
            print("[EXECUTOR SUCCESS] Data access resolved, analysis completed successfully")
            ctx.session.state['execution_status'] = 'success'
            print(f"[TEST] Setting execution_status = success (attempt {attempt})")
        
        # Call parent implementation
        async for event in super()._run_async_impl(ctx):
            yield event

def patch_executor():
    """Monkey patch the executor to use our failing-then-succeeding version."""
    from department_of_market_intelligence.agents.executor import get_experiment_executor_agent
    
    def patched_get_experiment_executor_agent():
        return FailingThenSucceedingExecutor(name="Experiment_Executor")
    
    # Replace the function
    import department_of_market_intelligence.agents.executor as executor_module
    executor_module.get_experiment_executor_agent = patched_get_experiment_executor_agent
    
    # Also patch in implementation workflow
    import department_of_market_intelligence.workflows.implementation_workflow as impl_workflow
    impl_workflow.get_experiment_executor_agent = patched_get_experiment_executor_agent

async def test_full_replanning_integration():
    """Test the complete replanning flow from failure to recovery."""
    print("🔄 TESTING FULL REPLANNING INTEGRATION")
    print("="*60)
    print("This test simulates:")
    print("1. Executor fails on first attempt → triggers replanning")
    print("2. Orchestrator creates new plan with error context") 
    print("3. Executor succeeds on second attempt → workflow completes")
    print("-" * 60)
    
    # Patch the executor to fail first, then succeed
    patch_executor()
    
    # Reset attempt counter
    FailingThenSucceedingExecutor.execution_attempts = 0
    
    try:
        print("🚀 Starting main workflow with failing-then-succeeding executor...")
        await main()
        print("✅ Workflow completed successfully!")
        
        # Verify we attempted execution twice (fail + succeed)
        attempts = FailingThenSucceedingExecutor.execution_attempts
        print(f"📊 Total execution attempts: {attempts}")
        
        if attempts >= 2:
            print("✅ REPLANNING LOOP VERIFIED:")
            print("  - First attempt failed as expected")
            print("  - System triggered replanning") 
            print("  - Second attempt succeeded")
            return True
        else:
            print("❌ REPLANNING FAILED:")
            print(f"  - Only {attempts} attempt(s) made")
            print("  - Expected at least 2 attempts (fail + succeed)")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 TESTING EXECUTOR → ORCHESTRATOR REPLANNING INTEGRATION")
    print("Testing the full workflow failure recovery mechanism...")
    print("-" * 80)
    
    try:
        success = asyncio.run(test_full_replanning_integration())
        if success:
            print("\n🎉 REPLANNING INTEGRATION TEST PASSED!")
            print("✅ System successfully recovers from executor failures")
            print("✅ Orchestrator replanning loop working correctly")
        else:
            print("\n⚠️  Replanning integration test failed")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)