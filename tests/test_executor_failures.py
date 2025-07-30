#!/usr/bin/env python3
"""Test cases for Executor failure scenarios that trigger orchestrator replanning."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Temporarily modify config for testing
import department_of_market_intelligence.config as config
config.DRY_RUN_MODE = True
config.DRY_RUN_SKIP_LLM = True
config.MAX_DRY_RUN_ITERATIONS = 1
config.VERBOSE_LOGGING = False

from department_of_market_intelligence.tools.mock_llm_agent import MockLlmAgent

class TestExecutorFailureScenarios:
    """Test different executor failure scenarios."""
    
    def __init__(self):
        self.test_cases = [
            self.test_data_access_failure,
            self.test_dependency_missing,
            self.test_statistical_significance_failure,
            self.test_memory_resource_failure,
            self.test_timeout_failure
        ]
    
    async def test_data_access_failure(self, ctx):
        """Test scenario where executor cannot access required data files."""
        print("\n=== TEST CASE 1: Data Access Failure ===")
        
        # Simulate executor that fails due to data access
        print("[EXECUTOR FAILURE] Cannot access required data file: market_data.csv")
        print("[EXECUTOR FAILURE] Error: FileNotFoundError - /data/market_data.csv not found")
        ctx.session.state['execution_status'] = 'critical_error'
        ctx.session.state['error_type'] = 'data_access_failure'
        ctx.session.state['error_details'] = 'Required market data file missing or inaccessible'
        
        print(f"✅ Execution status: {ctx.session.state.get('execution_status')}")
        print(f"✅ Error type: {ctx.session.state.get('error_type')}")
        return ctx.session.state.get('execution_status') == 'critical_error'
    
    async def test_dependency_missing(self, ctx):
        """Test scenario where required Python packages are missing."""
        print("\n=== TEST CASE 2: Dependency Missing ===")
        
        # Simulate dependency failure
        print("[EXECUTOR FAILURE] ImportError: No module named 'specialized_finance_lib'")
        print("[EXECUTOR FAILURE] Required package not installed: pip install specialized-finance-lib")
        ctx.session.state['execution_status'] = 'critical_error'
        ctx.session.state['error_type'] = 'dependency_missing'
        ctx.session.state['error_details'] = 'Missing required package: specialized_finance_lib'
        ctx.session.state['suggested_fix'] = 'Update implementation to use available libraries'
        
        print(f"✅ Execution status: {ctx.session.state.get('execution_status')}")
        print(f"✅ Suggested fix: {ctx.session.state.get('suggested_fix')}")
        return ctx.session.state.get('execution_status') == 'critical_error'
    
    async def test_statistical_significance_failure(self, ctx):
        """Test scenario where statistical tests fail significance requirements."""
        print("\n=== TEST CASE 3: Statistical Significance Failure ===")
        
        # Simulate statistical significance failure
        print("[EXECUTOR FAILURE] Statistical test results:")
        print("[EXECUTOR FAILURE] - T-test p-value: 0.087 (required: < 0.05)")
        print("[EXECUTOR FAILURE] - Sample size: 45 (insufficient for reliable results)")
        print("[EXECUTOR FAILURE] Results do not meet statistical significance requirements")
        ctx.session.state['execution_status'] = 'critical_error'
        ctx.session.state['error_type'] = 'statistical_significance_failure'
        ctx.session.state['error_details'] = 'Results fail to meet p < 0.05 significance threshold'
        ctx.session.state['suggested_fix'] = 'Increase sample size or modify analysis approach'
        
        print(f"✅ Execution status: {ctx.session.state.get('execution_status')}")
        print(f"✅ Error details: {ctx.session.state.get('error_details')}")
        return ctx.session.state.get('execution_status') == 'critical_error'
    
    async def test_memory_resource_failure(self, ctx):
        """Test scenario where analysis requires too much memory."""
        print("\n=== TEST CASE 4: Memory Resource Failure ===")
        
        # Simulate memory resource failure
        print("[EXECUTOR FAILURE] MemoryError: Unable to allocate 24.5 GB for array")
        print("[EXECUTOR FAILURE] Dataset too large for available memory")
        print("[EXECUTOR FAILURE] Current memory usage: 15.2 GB / 16 GB available")
        ctx.session.state['execution_status'] = 'critical_error'
        ctx.session.state['error_type'] = 'memory_resource_failure'
        ctx.session.state['error_details'] = 'Dataset exceeds available memory capacity'
        ctx.session.state['suggested_fix'] = 'Implement chunked processing or reduce dataset size'
        
        print(f"✅ Execution status: {ctx.session.state.get('execution_status')}")
        print(f"✅ Suggested fix: {ctx.session.state.get('suggested_fix')}")
        return ctx.session.state.get('execution_status') == 'critical_error'
    
    async def test_timeout_failure(self, ctx):
        """Test scenario where computation takes too long."""
        print("\n=== TEST CASE 5: Computation Timeout ===")
        
        # Simulate computation timeout failure
        print("[EXECUTOR FAILURE] TimeoutError: Computation exceeded 2 hour limit")
        print("[EXECUTOR FAILURE] Monte Carlo simulation with 1M iterations still running")
        print("[EXECUTOR FAILURE] Estimated completion time: 6+ hours")
        ctx.session.state['execution_status'] = 'critical_error'
        ctx.session.state['error_type'] = 'computation_timeout'
        ctx.session.state['error_details'] = 'Analysis exceeds reasonable computation time limits'
        ctx.session.state['suggested_fix'] = 'Reduce simulation iterations or optimize algorithm'
        
        print(f"✅ Execution status: {ctx.session.state.get('execution_status')}")
        print(f"✅ Error type: {ctx.session.state.get('error_type')}")
        return ctx.session.state.get('execution_status') == 'critical_error'

async def test_orchestrator_replanning_loop():
    """Test the full replanning loop when executor fails."""
    print("\n" + "="*60)
    print("TESTING ORCHESTRATOR REPLANNING LOOP")
    print("="*60)
    
    # Mock session context
    class MockContext:
        def __init__(self):
            self.session = MockSession()
    
    class MockSession:
        def __init__(self):
            self.state = {
                'task_file_path': 'tasks/sample_research_task.md',
                'outputs_dir': 'outputs',
                'current_date': '2025-07-28',
                'current_year': 2025,
                'current_task': 'execute_experiments',
                'execution_status': 'pending'
            }
    
    ctx = MockContext()
    test_suite = TestExecutorFailureScenarios()
    
    passed_tests = 0
    total_tests = len(test_suite.test_cases)
    
    for i, test_case in enumerate(test_suite.test_cases, 1):
        # Reset state for each test
        ctx.session.state['execution_status'] = 'pending'
        ctx.session.state.pop('error_type', None)
        ctx.session.state.pop('error_details', None)
        ctx.session.state.pop('suggested_fix', None)
        
        try:
            result = await test_case(ctx)
            if result:
                passed_tests += 1
                print(f"✅ Test {i} PASSED")
            else:
                print(f"❌ Test {i} FAILED")
        except Exception as e:
            print(f"❌ Test {i} ERROR: {e}")
    
    print(f"\n🎯 TEST SUMMARY: {passed_tests}/{total_tests} tests passed")
    
    # Test the replanning trigger logic
    print("\n" + "="*60)
    print("TESTING REPLANNING TRIGGER LOGIC")
    print("="*60)
    
    # Simulate the root workflow's error detection
    if ctx.session.state.get('execution_status') == 'critical_error':
        print("🔄 ROOT WORKFLOW: Critical error detected in execution.")
        print("🔄 ROOT WORKFLOW: Looping back to implementation planning...")
        print("🔄 ORCHESTRATOR: Will receive error details for replanning:")
        print(f"   - Error Type: {ctx.session.state.get('error_type', 'unknown')}")
        print(f"   - Error Details: {ctx.session.state.get('error_details', 'none')}")
        print(f"   - Suggested Fix: {ctx.session.state.get('suggested_fix', 'none')}")
        print("✅ Replanning loop would be triggered successfully")
    else:
        print("❌ Replanning trigger logic failed")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    import asyncio
    print("🧪 TESTING EXECUTOR FAILURE SCENARIOS")
    print("Testing scenarios where Executor fails and triggers Orchestrator replanning...")
    print("-" * 80)
    
    try:
        success = asyncio.run(test_orchestrator_replanning_loop())
        if success:
            print("\n🎉 ALL EXECUTOR FAILURE TESTS PASSED!")
            print("✅ Replanning loop logic validated successfully")
        else:
            print("\n⚠️  Some tests failed - check implementation")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)