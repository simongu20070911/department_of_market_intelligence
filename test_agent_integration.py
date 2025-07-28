#!/usr/bin/env python3
"""
Test SessionState integration with agents and checkpoint system.
"""

import asyncio
from google.adk.agents.invocation_context import InvocationContext
from google.adk.sessions import InMemorySessionService

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from .utils.state_model import SessionState
from .utils.state_adapter import StateAdapter, StateProxy
from .utils.checkpoint_manager import CheckpointManager
from agents.validators_updated import MetaValidatorCheckAgentV2, SeniorValidatorV2
import config


async def test_checkpoint_with_session_state():
    """Test checkpoint save/load with SessionState."""
    print("\n=== Testing Checkpoint Integration ===")
    
    # Create a SessionState
    session = SessionState(task_id="checkpoint_test")
    session.current_phase = "implementation"
    session.plan_artifact_name = "outputs/research_plan_v1.md"
    session.validation_info.validation_status = "approved"
    session.validation_info.validation_version = 3
    
    # Create checkpoint manager
    cm = CheckpointManager(task_id="checkpoint_test")
    
    # Save checkpoint with SessionState
    checkpoint_id = cm.create_checkpoint(
        phase="implementation",
        step="validation_complete",
        session_state=session,
        metadata={"test_run": True}
    )
    
    print(f"✓ Created checkpoint: {checkpoint_id}")
    
    # Load checkpoint as dict (backward compatibility)
    checkpoint_data = cm.load_checkpoint(checkpoint_id, return_session_state=False)
    print(f"✓ Loaded as dict with {len(checkpoint_data['session_state'])} keys")
    
    # Load checkpoint as SessionState
    loaded_session = cm.load_checkpoint(checkpoint_id, return_session_state=True)
    print(f"✓ Loaded as SessionState:")
    print(f"  - Task ID: {loaded_session.task_id}")
    print(f"  - Phase: {loaded_session.current_phase}")
    print(f"  - Validation status: {loaded_session.get_validation_status()}")
    print(f"  - Validation version: {loaded_session.validation_info.validation_version}")
    
    # Verify data integrity
    assert loaded_session.task_id == session.task_id
    assert loaded_session.current_phase == session.current_phase
    assert loaded_session.get_validation_status() == session.get_validation_status()
    
    return checkpoint_id


async def test_agent_with_session_state():
    """Test agent execution with SessionState."""
    print("\n=== Testing Agent with SessionState ===")
    
    # Create a session and context
    session_service = InMemorySessionService()
    session = await session_service.create_session("test_session")
    ctx = InvocationContext(session=session)
    
    # Create SessionState
    state = SessionState(task_id="agent_test")
    state.validation_info.validation_status = "rejected"  # Will continue loop
    
    # Test 1: Direct SessionState
    print("\nTest 1: Direct SessionState")
    ctx.session.state = state
    agent = MetaValidatorCheckAgentV2(name="MetaValidator_Direct")
    
    events = []
    async for event in agent.run_async(ctx):
        events.append(event)
    
    print(f"✓ Agent executed with SessionState")
    print(f"  - Should escalate: {events[0].actions.escalate}")
    assert events[0].actions.escalate == False  # rejected status continues loop
    
    # Test 2: Legacy dict state
    print("\nTest 2: Legacy dict state")
    dict_state = {
        'validation_status': 'approved',
        'task_id': 'agent_test'
    }
    ctx.session.state = dict_state
    
    events = []
    async for event in agent.run_async(ctx):
        events.append(event)
    
    print(f"✓ Agent executed with dict state")
    print(f"  - Should escalate: {events[0].actions.escalate}")
    assert events[0].actions.escalate == True  # approved status escalates
    
    # Test 3: StateProxy
    print("\nTest 3: StateProxy wrapper")
    state.set_validation_status('critical_error')
    proxy = StateAdapter.create_proxy_state(state)
    ctx.session.state = proxy
    
    events = []
    async for event in agent.run_async(ctx):
        events.append(event)
    
    print(f"✓ Agent executed with StateProxy")
    print(f"  - Should escalate: {events[0].actions.escalate}")
    print(f"  - Execution status: {state.get_execution_status()}")
    assert events[0].actions.escalate == True
    assert state.get_execution_status() == 'critical_error'


async def test_senior_validator_v2():
    """Test the fully migrated SeniorValidatorV2."""
    print("\n=== Testing SeniorValidatorV2 ===")
    
    # Set dry run mode for testing
    original_dry_run = config.DRY_RUN_MODE
    config.DRY_RUN_MODE = True
    
    try:
        # Create context with SessionState
        session_service = InMemorySessionService()
        session = await session_service.create_session("validator_session")
        ctx = InvocationContext(session=session)
        
        state = SessionState(task_id="validator_test")
        state.artifact_to_validate = "outputs/test_artifact.md"
        state.validation_info.validation_version = 5
        ctx.session.state = state
        
        # Run the validator
        validator = SeniorValidatorV2()
        
        events = []
        async for event in validator.run_async(ctx):
            events.append(event)
        
        print(f"✓ SeniorValidatorV2 executed successfully")
        print(f"  - Validation status: {state.get_validation_status()}")
        print(f"  - Senior critique: {state.validation_info.senior_critique_artifact}")
        
        assert state.get_validation_status() == 'approved'
        assert state.validation_info.senior_critique_artifact == 'outputs/senior_critique_v5.md'
        
    finally:
        config.DRY_RUN_MODE = original_dry_run


async def test_state_proxy_with_agents():
    """Test StateProxy provides full compatibility."""
    print("\n=== Testing StateProxy Compatibility ===")
    
    # Create SessionState and proxy
    state = SessionState(task_id="proxy_test")
    proxy = StateAdapter.create_proxy_state(state)
    
    # Test dict-like operations that agents might use
    proxy['artifact_to_validate'] = 'outputs/test.md'
    proxy['validation_version'] = 10
    proxy['custom_key'] = 'custom_value'
    
    print(f"✓ Set values through proxy")
    print(f"  - artifact: {proxy['artifact_to_validate']}")
    print(f"  - version: {proxy['validation_version']}")
    print(f"  - custom: {proxy.get('custom_key')}")
    
    # Verify changes in underlying SessionState
    assert state.artifact_to_validate == 'outputs/test.md'
    assert state.validation_info.validation_version == 10
    assert state.metadata['custom_key'] == 'custom_value'
    
    # Test .keys() method
    keys = proxy.keys()
    print(f"✓ Proxy keys(): {len(keys)} keys available")
    assert 'artifact_to_validate' in keys
    assert 'validation_version' in keys
    
    print("✓ StateProxy provides full backward compatibility")


async def main():
    """Run all integration tests."""
    print("Testing SessionState Integration with Agents")
    print("=" * 50)
    
    try:
        # Run tests
        checkpoint_id = await test_checkpoint_with_session_state()
        await test_agent_with_session_state()
        await test_senior_validator_v2()
        await test_state_proxy_with_agents()
        
        print("\n" + "=" * 50)
        print("✅ All integration tests passed!")
        
        print("\n📝 Migration Guidelines:")
        print("\n1. For new agents:")
        print("   - Extend SessionStateAwareAgent base class")
        print("   - Use get_session_state() and update_session_state()")
        print("   - Access fields with type safety: session.validation_info.status")
        
        print("\n2. For existing agents (minimal changes):")
        print("   - Use StateProxy: proxy = StateAdapter.create_proxy_state(session)")
        print("   - Continue using state['key'] syntax")
        print("   - Proxy handles the translation automatically")
        
        print("\n3. For checkpoint system:")
        print("   - CheckpointManager now handles both dict and SessionState")
        print("   - Use return_session_state=True when loading for new agents")
        print("   - Backward compatible with existing checkpoints")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Use asyncio.run() for Python 3.7+
    asyncio.run(main())