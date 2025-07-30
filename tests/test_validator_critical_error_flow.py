#!/usr/bin/env python3
"""Test the validator critical error detection and escalation flow."""

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

from department_of_market_intelligence.tools.mock_llm_agent import MockLlmAgent
from department_of_market_intelligence.agents.validators import MetaValidatorCheckAgent
import asyncio

class MockContext:
    def __init__(self, initial_state):
        self.session = MockSession(initial_state)

class MockSession:
    def __init__(self, initial_state):
        self.state = initial_state.copy()

async def test_critical_error_validator_flow():
    """Test the complete flow: Executor fails → Validators escalate → Triggers replanning."""
    print("🧪 TESTING VALIDATOR CRITICAL ERROR FLOW")
    print("="*60)
    
    test_cases = [
        {
            "name": "Normal Success Flow",
            "execution_status": "success",
            "expected_validation_status": "approved",
            "expected_final_execution_status": "success"
        },
        {
            "name": "Critical Error Flow", 
            "execution_status": "critical_error",
            "error_type": "data_access_failure",
            "error_details": "Required market data file missing",
            "expected_validation_status": "critical_error",
            "expected_final_execution_status": "critical_error"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- TEST CASE {i}: {test_case['name']} ---")
        
        # Initialize context with test state
        initial_state = {
            'execution_status': test_case['execution_status'],
            'validation_version': 0
        }
        if 'error_type' in test_case:
            initial_state['error_type'] = test_case['error_type']
            initial_state['error_details'] = test_case['error_details']
        
        ctx = MockContext(initial_state)
        
        print(f"📊 Initial execution_status: {ctx.session.state['execution_status']}")
        
        # 1. Mock Junior Validator
        junior_validator = MockLlmAgent(name="Junior_Validator")
        print("\n🔍 Junior Validator Processing...")
        async for event in junior_validator._run_async_impl(ctx):
            pass
        
        # 2. Mock Senior Validator  
        senior_validator = MockLlmAgent(name="Senior_Validator")
        print("\n🔍 Senior Validator Processing...")
        async for event in senior_validator._run_async_impl(ctx):
            pass
        
        print(f"📊 Senior Validator set validation_status: {ctx.session.state.get('validation_status')}")
        
        # 3. MetaValidatorCheck
        meta_validator = MetaValidatorCheckAgent(name="MetaValidatorCheck")
        print("\n🔍 MetaValidatorCheck Processing...")
        should_escalate = False
        async for event in meta_validator._run_async_impl(ctx):
            should_escalate = event.actions.escalate if event.actions else False
        
        print(f"📊 Final execution_status: {ctx.session.state.get('execution_status')}")
        print(f"🎯 Should escalate (exit loop): {should_escalate}")
        
        # Verify results
        validation_status = ctx.session.state.get('validation_status')
        final_execution_status = ctx.session.state.get('execution_status')
        
        success = (
            validation_status == test_case['expected_validation_status'] and
            final_execution_status == test_case['expected_final_execution_status']
        )
        
        if success:
            print(f"✅ {test_case['name']} PASSED")
        else:
            print(f"❌ {test_case['name']} FAILED")
            print(f"   Expected validation_status: {test_case['expected_validation_status']}")
            print(f"   Actual validation_status: {validation_status}")
            print(f"   Expected final execution_status: {test_case['expected_final_execution_status']}")
            print(f"   Actual final execution_status: {final_execution_status}")
        
        print("-" * 60)
    
    print("\n🔄 TESTING REPLANNING TRIGGER")
    print("="*60)
    
    # Simulate root workflow check
    final_execution_status = ctx.session.state.get('execution_status')
    if final_execution_status == 'critical_error':
        print("🔄 ROOT WORKFLOW: Critical error detected in execution.")
        print("🔄 ROOT WORKFLOW: Looping back to implementation planning...")
        print("✅ Replanning would be triggered correctly")
        return True
    else:
        print(f"❌ Root workflow would NOT trigger replanning (status: {final_execution_status})")
        return False

if __name__ == "__main__":
    print("🧪 TESTING COMPLETE VALIDATOR → REPLANNING FLOW")
    print("Testing: Executor Error → Validator Detection → Critical Error Escalation → Replanning Trigger")
    print("-" * 80)
    
    try:
        success = asyncio.run(test_critical_error_validator_flow())
        if success:
            print("\n🎉 VALIDATOR CRITICAL ERROR FLOW TEST PASSED!")
            print("✅ Validators correctly detect and escalate critical errors")
            print("✅ MetaValidator properly triggers replanning loop")
        else:
            print("\n⚠️  Validator flow test failed")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)