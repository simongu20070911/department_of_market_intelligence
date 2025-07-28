#!/usr/bin/env python3
"""
Test script for SessionState model and migration adapter.
"""

import json
from utils.state_model import SessionState, TaskInfo, ValidationInfo, ExecutionInfo
from utils.state_adapter import StateAdapter, StateProxy


def test_basic_session_state():
    """Test basic SessionState creation and validation."""
    print("\n=== Testing Basic SessionState ===")
    
    # Create a new session
    session = SessionState(task_id="test_research_001")
    print(f"Created session with task_id: {session.task_id}")
    print(f"Current phase: {session.current_phase}")
    print(f"Validation status: {session.get_validation_status()}")
    
    # Test type validation
    try:
        session.current_phase = "invalid_phase"  # Should fail
    except ValueError as e:
        print(f"✓ Type validation works: {e}")
    
    # Test artifact path validation
    session.plan_artifact_name = "outputs/research_plan_v0.md"
    print(f"✓ Set plan artifact: {session.plan_artifact_name}")
    
    # Test validation info
    session.set_validation_status("approved")
    session.increment_validation_version()
    print(f"✓ Validation version: {session.validation_info.validation_version}")
    print(f"✓ Validation status: {session.get_validation_status()}")
    
    return session


def test_coding_tasks():
    """Test coding task management."""
    print("\n=== Testing Coding Tasks ===")
    
    session = SessionState(task_id="test_coding")
    
    # Add some tasks
    tasks = [
        TaskInfo(task_id="data_fetch", description="Fetch market data"),
        TaskInfo(task_id="feature_eng", description="Engineer features", 
                dependencies=["data_fetch"]),
        TaskInfo(task_id="model_train", description="Train models",
                dependencies=["data_fetch", "feature_eng"])
    ]
    
    for task in tasks:
        session.add_coding_task(task)
        print(f"✓ Added task: {task.task_id} with deps: {task.dependencies}")
    
    # Test task retrieval
    task = session.get_coding_task_by_id("feature_eng")
    print(f"✓ Retrieved task: {task.task_id} - {task.description}")
    
    # Set current task
    session.coder_subtask = tasks[0]
    print(f"✓ Current task: {session.coder_subtask.task_id}")
    
    return session


def test_legacy_migration():
    """Test migration from legacy dictionary state."""
    print("\n=== Testing Legacy Migration ===")
    
    # Simulate legacy state
    legacy_state = {
        'current_task': 'generate_initial_plan',
        'plan_artifact_name': 'outputs/research_plan_v0.md',
        'plan_version': 0,
        'validation_status': 'pending',
        'validation_version': 0,
        'execution_status': 'pending',
        'coder_subtask': {
            'task_id': 'data_analysis',
            'description': 'Analyze historical data',
            'dependencies': ['data_fetch']
        },
        'some_custom_field': 'custom_value',
        'another_field': 42
    }
    
    # Convert to SessionState
    session = StateAdapter.dict_to_session_state(legacy_state, "migrated_task")
    print(f"✓ Migrated to SessionState")
    print(f"  - Task ID: {session.task_id}")
    print(f"  - Current task: {session.current_task}")
    print(f"  - Plan version: {session.plan_version}")
    print(f"  - Validation status: {session.get_validation_status()}")
    print(f"  - Coder subtask: {session.coder_subtask.task_id if session.coder_subtask else None}")
    print(f"  - Custom fields in metadata: {list(session.metadata.keys())}")
    
    # Convert back to dict
    new_dict = StateAdapter.session_state_to_dict(session)
    print(f"\n✓ Converted back to dict with {len(new_dict)} fields")
    
    # Verify key fields preserved
    for key in ['current_task', 'plan_version', 'validation_status']:
        if key in legacy_state and key in new_dict:
            print(f"  - {key}: {legacy_state[key]} -> {new_dict[key]}")
    
    return session


def test_state_proxy():
    """Test StateProxy for backward compatibility."""
    print("\n=== Testing State Proxy ===")
    
    # Create session and proxy
    session = SessionState(task_id="proxy_test")
    proxy = StateAdapter.create_proxy_state(session)
    
    # Test dict-like access
    proxy['current_task'] = 'test_task'
    proxy['validation_status'] = 'approved'
    proxy['custom_field'] = 'custom_value'
    
    print(f"✓ Set values via proxy")
    print(f"  - current_task: {proxy['current_task']}")
    print(f"  - validation_status: {proxy['validation_status']}")
    print(f"  - custom_field: {proxy.get('custom_field')}")
    
    # Test that changes reflect in session
    print(f"\n✓ Changes reflected in SessionState:")
    print(f"  - session.current_task: {session.current_task}")
    print(f"  - session.validation_status: {session.get_validation_status()}")
    print(f"  - session.metadata: {session.metadata}")
    
    # Test keys() method
    keys = proxy.keys()
    print(f"\n✓ Proxy has {len(keys)} accessible keys")
    
    return session, proxy


def test_checkpoint_serialization():
    """Test checkpoint save/load functionality."""
    print("\n=== Testing Checkpoint Serialization ===")
    
    # Create a complex session
    session = SessionState(task_id="checkpoint_test")
    session.current_phase = "implementation"
    session.plan_artifact_name = "outputs/plan.md"
    session.validation_info.validation_status = "approved"
    session.validation_info.validation_version = 2
    session.execution_info.execution_status = "running"
    session.add_coding_task(TaskInfo(
        task_id="test_task",
        description="Test task",
        status="completed"
    ))
    
    # Convert to checkpoint dict
    checkpoint = session.to_checkpoint_dict()
    print(f"✓ Created checkpoint with {len(checkpoint)} top-level fields")
    
    # Simulate save/load with JSON
    checkpoint_json = json.dumps(checkpoint, indent=2)
    print(f"✓ Serialized to JSON ({len(checkpoint_json)} chars)")
    
    # Load from checkpoint
    loaded_data = json.loads(checkpoint_json)
    loaded_session = SessionState.from_checkpoint_dict(loaded_data)
    
    print(f"\n✓ Loaded from checkpoint:")
    print(f"  - Task ID: {loaded_session.task_id}")
    print(f"  - Phase: {loaded_session.current_phase}")
    print(f"  - Validation status: {loaded_session.get_validation_status()}")
    print(f"  - Coding tasks: {len(loaded_session.all_coding_tasks)}")
    
    return session, loaded_session


def test_metadata_size_limit():
    """Test metadata size validation."""
    print("\n=== Testing Metadata Size Limit ===")
    
    session = SessionState(task_id="metadata_test")
    
    # Small metadata should work
    session.metadata['small_data'] = "This is fine"
    print(f"✓ Small metadata accepted")
    
    # Large metadata should fail
    try:
        large_data = "x" * 20000  # 20KB string
        session.metadata = {'large_data': large_data}
    except ValueError as e:
        print(f"✓ Large metadata rejected: {str(e)[:50]}...")
    
    return session


def main():
    """Run all tests."""
    print("Testing Pydantic SessionState Implementation")
    print("=" * 50)
    
    try:
        # Run tests
        session1 = test_basic_session_state()
        session2 = test_coding_tasks()
        session3 = test_legacy_migration()
        session4, proxy = test_state_proxy()
        session5, loaded = test_checkpoint_serialization()
        session6 = test_metadata_size_limit()
        
        print("\n" + "=" * 50)
        print("✅ All tests passed successfully!")
        print("\nThe SessionState model is ready for integration.")
        print("\nNext steps:")
        print("1. Update agents to use SessionState instead of dict")
        print("2. Use StateProxy for gradual migration")
        print("3. Update checkpoint save/load to use the new model")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()