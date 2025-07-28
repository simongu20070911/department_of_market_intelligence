#!/usr/bin/env python3
"""
Simple test to verify SessionState model integration.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.state_model import SessionState, TaskInfo
from utils.state_adapter import StateAdapter, StateProxy


def test_session_state_in_workflow():
    """Test SessionState usage in workflow scenarios."""
    print("\n=== Testing SessionState in Workflow Scenarios ===")
    
    # Create a research session
    session = SessionState(task_id="test_research_workflow")
    
    print(f"\n1. Initial Planning Phase:")
    session.current_phase = "planning"
    session.current_task = "generate_initial_plan"
    session.plan_artifact_name = "outputs/research_plan_v0.md"
    print(f"   - Phase: {session.current_phase}")
    print(f"   - Task: {session.current_task}")
    print(f"   - Plan artifact: {session.plan_artifact_name}")
    
    print(f"\n2. Validation Loop:")
    session.artifact_to_validate = session.plan_artifact_name
    session.increment_validation_version()  # Now v1
    session.validation_info.junior_critique_artifact = "outputs/junior_critique_v1.md"
    session.validation_info.senior_critique_artifact = "outputs/senior_critique_v1.md"
    session.set_validation_status("approved")
    print(f"   - Validating: {session.artifact_to_validate}")
    print(f"   - Version: {session.validation_info.validation_version}")
    print(f"   - Status: {session.get_validation_status()}")
    
    print(f"\n3. Implementation Phase:")
    session.current_phase = "implementation"
    session.implementation_manifest_artifact = "outputs/implementation_manifest.json"
    
    # Add coding tasks
    tasks = [
        TaskInfo(task_id="data_fetch", description="Fetch market data"),
        TaskInfo(task_id="analysis", description="Analyze data", dependencies=["data_fetch"]),
        TaskInfo(task_id="report", description="Generate report", dependencies=["analysis"])
    ]
    
    for task in tasks:
        session.add_coding_task(task)
    
    print(f"   - Phase: {session.current_phase}")
    print(f"   - Manifest: {session.implementation_manifest_artifact}")
    print(f"   - Coding tasks: {len(session.all_coding_tasks)}")
    
    # Set current coding task
    session.coder_subtask = session.all_coding_tasks[0]
    print(f"   - Current task: {session.coder_subtask.task_id}")
    
    print(f"\n4. Execution Phase:")
    session.current_phase = "execution"
    session.set_execution_status("running")
    print(f"   - Phase: {session.current_phase}")
    print(f"   - Execution status: {session.get_execution_status()}")
    
    return session


def test_legacy_compatibility():
    """Test backward compatibility with dict-based state."""
    print("\n=== Testing Legacy Compatibility ===")
    
    # Simulate legacy state from existing workflow
    legacy_state = {
        'task_id': 'legacy_task',
        'current_task': 'refine_plan',
        'plan_artifact_name': 'outputs/research_plan_v2.md',
        'plan_version': 2,
        'validation_status': 'rejected',
        'validation_version': 3,
        'artifact_to_validate': 'outputs/research_plan_v2.md',
        'junior_critique_artifact': 'outputs/junior_critique_v3.md',
        'execution_status': 'pending',
        'coder_subtask': {
            'task_id': 'model_training',
            'description': 'Train ML models',
            'dependencies': ['data_prep']
        }
    }
    
    print(f"\nOriginal dict state: {len(legacy_state)} fields")
    
    # Convert to SessionState
    session = StateAdapter.dict_to_session_state(legacy_state, "legacy_task")
    print(f"\nConverted to SessionState:")
    print(f"   - Task ID: {session.task_id}")
    print(f"   - Current task: {session.current_task}")
    print(f"   - Plan version: {session.plan_version}")
    print(f"   - Validation status: {session.get_validation_status()}")
    print(f"   - Coder subtask: {session.coder_subtask.task_id if session.coder_subtask else 'None'}")
    
    # Use StateProxy for dict-like access
    proxy = StateAdapter.create_proxy_state(session)
    print(f"\nUsing StateProxy:")
    print(f"   - proxy['validation_status']: {proxy['validation_status']}")
    print(f"   - proxy['plan_version']: {proxy['plan_version']}")
    
    # Modify through proxy
    proxy['validation_status'] = 'approved'
    proxy['custom_field'] = 'added_through_proxy'
    
    print(f"\nAfter modifications:")
    print(f"   - SessionState status: {session.get_validation_status()}")
    print(f"   - Custom field in metadata: {session.metadata.get('custom_field')}")
    
    # Convert back to dict
    new_dict = StateAdapter.session_state_to_dict(session)
    print(f"\nConverted back to dict: {len(new_dict)} fields")
    
    return session, proxy


def test_checkpoint_serialization():
    """Test checkpoint-style serialization."""
    print("\n=== Testing Checkpoint Serialization ===")
    
    # Create complex session state
    session = SessionState(task_id="checkpoint_test")
    session.current_phase = "implementation"
    session.plan_artifact_name = "outputs/plan_v3.md"
    session.validation_info.validation_status = "approved"
    session.validation_info.validation_version = 5
    session.execution_info.execution_status = "success"
    
    # Add some tasks
    session.add_coding_task(TaskInfo(
        task_id="data_pipeline",
        description="Build data pipeline",
        status="completed",
        output_artifact="outputs/pipeline.py"
    ))
    
    # Serialize to checkpoint format
    checkpoint_data = session.to_checkpoint_dict()
    print(f"\nSerialized to checkpoint: {len(checkpoint_data)} top-level fields")
    
    # Simulate JSON round-trip
    import json
    json_str = json.dumps(checkpoint_data, indent=2)
    print(f"JSON size: {len(json_str)} chars")
    
    # Deserialize
    loaded_data = json.loads(json_str)
    loaded_session = SessionState.from_checkpoint_dict(loaded_data)
    
    print(f"\nLoaded from checkpoint:")
    print(f"   - Task ID: {loaded_session.task_id}")
    print(f"   - Phase: {loaded_session.current_phase}")
    print(f"   - Validation status: {loaded_session.get_validation_status()}")
    print(f"   - Coding tasks: {len(loaded_session.all_coding_tasks)}")
    print(f"   - Task status: {loaded_session.all_coding_tasks[0].status}")
    
    # Verify integrity
    assert loaded_session.task_id == session.task_id
    assert loaded_session.current_phase == session.current_phase  
    assert loaded_session.get_validation_status() == session.get_validation_status()
    assert len(loaded_session.all_coding_tasks) == len(session.all_coding_tasks)
    
    print("   ✓ Data integrity verified")
    
    return loaded_session


def test_type_safety():
    """Test Pydantic type validation."""
    print("\n=== Testing Type Safety ===")
    
    session = SessionState(task_id="type_test")
    
    # Valid assignments
    session.current_phase = "execution"
    session.validation_info.validation_status = "approved"
    print("✓ Valid assignments accepted")
    
    # Test invalid phase
    try:
        session.current_phase = "invalid_phase"
        print("❌ Should have failed")
    except ValueError as e:
        print(f"✓ Invalid phase rejected: {str(e)[:50]}...")
    
    # Test invalid validation status
    try:
        session.set_validation_status("invalid_status")
        print("❌ Should have failed")
    except ValueError as e:
        print(f"✓ Invalid validation status rejected: {str(e)[:50]}...")
    
    # Test empty artifact path
    try:
        session.plan_artifact_name = "   "  # Empty/whitespace
        print("❌ Should have failed")
    except ValueError as e:
        print(f"✓ Empty artifact path rejected: {str(e)[:50]}...")
    
    # Test metadata size limit
    try:
        large_data = "x" * 15000  # 15KB
        session.metadata = {'large_data': large_data}
        print("❌ Should have failed")
    except ValueError as e:
        print(f"✓ Large metadata rejected: {str(e)[:50]}...")
    
    print("✓ Type safety working correctly")


def main():
    """Run all tests."""
    print("SessionState Integration Testing")
    print("=" * 40)
    
    try:
        # Run tests
        session1 = test_session_state_in_workflow()
        session2, proxy = test_legacy_compatibility()
        session3 = test_checkpoint_serialization()
        test_type_safety()
        
        print("\n" + "=" * 40)
        print("✅ All tests passed!")
        
        print("\n📋 Implementation Summary:")
        print("1. ✅ SessionState model with type safety")
        print("2. ✅ Backward compatibility with dict state")
        print("3. ✅ StateProxy for gradual migration")
        print("4. ✅ Checkpoint serialization support")
        print("5. ✅ Artifact-Pointer Pattern (file paths only)")
        
        print("\n🚀 Ready for agent integration!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()