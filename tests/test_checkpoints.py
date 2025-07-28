#!/usr/bin/env python3
"""
Comprehensive test of checkpoint system functionality.
Tests creation, recovery, SessionState compatibility, and output snapshots.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import json
import shutil
from datetime import datetime
from utils.checkpoint_manager import CheckpointManager
from utils.state_model import SessionState
from utils.state_adapter import StateAdapter
import config


def test_checkpoint_creation_and_recovery():
    """Test basic checkpoint creation and recovery."""
    print("\n=== Testing Checkpoint Creation and Recovery ===")
    
    # Create a test checkpoint manager
    test_task_id = "checkpoint_test_task"
    checkpoint_manager = CheckpointManager(test_task_id)
    
    # Create sample session state
    sample_session_state = SessionState(task_id=test_task_id)
    sample_session_state.current_phase = "implementation"
    sample_session_state.current_task = "generate_code"
    sample_session_state.plan_artifact_name = "outputs/test_plan.md"
    sample_session_state.metadata["test_field"] = "test_value"
    
    print(f"✓ Created SessionState with task_id: {sample_session_state.task_id}")
    
    # Test checkpoint creation
    checkpoint_id = checkpoint_manager.create_checkpoint(
        phase="implementation",
        step="code_generation",
        session_state=sample_session_state,
        metadata={"test_run": True, "agent_type": "test"}
    )
    
    print(f"✓ Created checkpoint: {checkpoint_id}")
    
    # Test checkpoint recovery
    recovered_data = checkpoint_manager.load_checkpoint(checkpoint_id)
    
    if recovered_data:
        print(f"✓ Recovered checkpoint data with {len(recovered_data['session_state'])} state fields")
        print(f"  - Phase: {recovered_data['phase']}")
        print(f"  - Step: {recovered_data['step']}")
        print(f"  - Uses SessionState: {recovered_data.get('uses_session_state_model', False)}")
    else:
        print("❌ Failed to recover checkpoint")
        return False
    
    # Test SessionState recovery
    recovered_session_state = checkpoint_manager.load_checkpoint(checkpoint_id, return_session_state=True)
    
    if isinstance(recovered_session_state, SessionState):
        print(f"✓ Recovered as SessionState: {recovered_session_state.task_id}")
        print(f"  - Current phase: {recovered_session_state.current_phase}")
        print(f"  - Current task: {recovered_session_state.current_task}")
        print(f"  - Plan artifact: {recovered_session_state.plan_artifact_name}")
        print(f"  - Metadata: {recovered_session_state.metadata}")
        
        # Verify data integrity
        assert recovered_session_state.task_id == sample_session_state.task_id
        assert recovered_session_state.current_phase == sample_session_state.current_phase
        assert recovered_session_state.current_task == sample_session_state.current_task
        assert recovered_session_state.plan_artifact_name == sample_session_state.plan_artifact_name
        assert recovered_session_state.metadata["test_field"] == "test_value"
        
        print("✓ Data integrity verified")
    else:
        print("❌ Failed to recover as SessionState")
        return False
    
    return True


def test_legacy_dict_checkpoint_recovery():
    """Test recovery from legacy dictionary-based checkpoints."""
    print("\n=== Testing Legacy Dict Checkpoint Recovery ===")
    
    test_task_id = "legacy_test_task"
    checkpoint_manager = CheckpointManager(test_task_id)
    
    # Create a legacy-style dict state
    legacy_state = {
        'task_id': test_task_id,
        'current_task': 'validate_results',
        'plan_artifact_name': 'outputs/legacy_plan.md',
        'plan_version': 3,
        'validation_status': 'approved',
        'validation_version': 2,
        'execution_status': 'success',
        'artifact_to_validate': 'outputs/results.json'
    }
    
    print(f"✓ Created legacy dict state with {len(legacy_state)} fields")
    
    # Create checkpoint with dict state
    checkpoint_id = checkpoint_manager.create_checkpoint(
        phase="results_validation",
        step="validation_complete",
        session_state=legacy_state,
        metadata={"legacy_test": True}
    )
    
    print(f"✓ Created legacy checkpoint: {checkpoint_id}")
    
    # Test recovery as SessionState
    recovered_session_state = checkpoint_manager.load_checkpoint(checkpoint_id, return_session_state=True)
    
    if isinstance(recovered_session_state, SessionState):
        print(f"✓ Successfully converted legacy checkpoint to SessionState")
        print(f"  - Task ID: {recovered_session_state.task_id}")
        print(f"  - Current task: {recovered_session_state.current_task}")
        print(f"  - Plan version: {recovered_session_state.plan_version}")
        print(f"  - Validation status: {recovered_session_state.get_validation_status()}")
        
        # Verify conversion worked correctly
        assert recovered_session_state.task_id == test_task_id
        assert recovered_session_state.current_task == 'validate_results'
        assert recovered_session_state.plan_version == 3
        assert recovered_session_state.get_validation_status() == 'approved'
        
        print("✓ Legacy conversion verified")
    else:
        print("❌ Failed to convert legacy checkpoint")
        return False
    
    return True


def test_checkpoint_listing_and_cleanup():
    """Test checkpoint listing and cleanup functionality."""
    print("\n=== Testing Checkpoint Listing and Cleanup ===")
    
    test_task_id = "cleanup_test_task"
    checkpoint_manager = CheckpointManager(test_task_id)
    
    # Create multiple checkpoints
    checkpoints = []
    for i in range(5):
        session_state = SessionState(task_id=test_task_id)
        session_state.current_phase = "testing"
        session_state.current_task = f"test_step_{i}"
        session_state.metadata["step_number"] = str(i)
        
        checkpoint_id = checkpoint_manager.create_checkpoint(
            phase="testing",
            step=f"step_{i}",
            session_state=session_state,
            metadata={"step": i}
        )
        checkpoints.append(checkpoint_id)
        print(f"✓ Created checkpoint {i+1}/5: {checkpoint_id}")
    
    # Test listing
    checkpoint_list = checkpoint_manager.list_checkpoints()
    print(f"✓ Listed {len(checkpoint_list)} checkpoints")
    
    if len(checkpoint_list) >= 5:
        print("✓ All checkpoints found in listing")
        
        # Verify sorting (newest first)
        timestamps = [cp["timestamp"] for cp in checkpoint_list]
        sorted_timestamps = sorted(timestamps, reverse=True)
        if timestamps == sorted_timestamps:
            print("✓ Checkpoints properly sorted by timestamp")
        else:
            print("❌ Checkpoint sorting failed")
            return False
    else:
        print(f"❌ Expected at least 5 checkpoints, found {len(checkpoint_list)}")
        return False
    
    # Test cleanup
    initial_count = len(checkpoint_list)
    keep_count = 3
    checkpoint_manager.cleanup_old_checkpoints(keep_count=keep_count)
    
    updated_list = checkpoint_manager.list_checkpoints()
    print(f"✓ After cleanup: {len(updated_list)} checkpoints (kept {keep_count})")
    
    if len(updated_list) <= keep_count:
        print("✓ Cleanup working correctly")
    else:
        print(f"❌ Cleanup failed - expected {keep_count}, got {len(updated_list)}")
        return False
    
    return True


def test_output_snapshots():
    """Test output directory snapshot functionality."""
    print("\n=== Testing Output Snapshots ===")
    
    test_task_id = "snapshot_test_task"
    checkpoint_manager = CheckpointManager(test_task_id)
    
    # Create some test files in outputs directory
    outputs_dir = checkpoint_manager.outputs_dir
    os.makedirs(outputs_dir, exist_ok=True)
    
    test_files = {
        "research_plan.md": "# Test Research Plan\nThis is a test plan.",
        "results.json": '{"test": "data", "value": 123}',
        "analysis.py": "# Test analysis script\nprint('Hello, world!')"
    }
    
    for filename, content in test_files.items():
        file_path = os.path.join(outputs_dir, filename)
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"✓ Created test file: {filename}")
    
    # Create checkpoint (which should create snapshot)
    session_state = SessionState(task_id=test_task_id)
    session_state.current_phase = "snapshot_test"
    session_state.current_task = "test_snapshots"
    
    checkpoint_id = checkpoint_manager.create_checkpoint(
        phase="snapshot_test",
        step="files_created",
        session_state=session_state,
        metadata={"file_count": len(test_files)}
    )
    
    print(f"✓ Created checkpoint with snapshot: {checkpoint_id}")
    
    # Verify snapshot directory exists
    snapshot_dir = os.path.join(
        checkpoint_manager.checkpoints_dir,
        f"outputs_snapshot_{checkpoint_id}"
    )
    
    if os.path.exists(snapshot_dir):
        print("✓ Snapshot directory created")
        
        # Verify files were copied
        snapshot_files = os.listdir(snapshot_dir)
        if set(snapshot_files) == set(test_files.keys()):
            print(f"✓ All {len(test_files)} files copied to snapshot")
            
            # Verify file contents
            all_contents_match = True
            for filename, expected_content in test_files.items():
                snapshot_file_path = os.path.join(snapshot_dir, filename)
                with open(snapshot_file_path, 'r') as f:
                    actual_content = f.read()
                if actual_content != expected_content:
                    print(f"❌ Content mismatch for {filename}")
                    all_contents_match = False
            
            if all_contents_match:
                print("✓ All file contents match in snapshot")
            else:
                return False
        else:
            print(f"❌ File mismatch - expected {set(test_files.keys())}, got {set(snapshot_files)}")
            return False
    else:
        print("❌ Snapshot directory not created")
        return False
    
    # Test snapshot restoration
    # First, modify the original files
    modified_content = "# MODIFIED FILE"
    for filename in test_files.keys():
        file_path = os.path.join(outputs_dir, filename)
        with open(file_path, 'w') as f:
            f.write(modified_content)
    
    print("✓ Modified original files")
    
    # Restore from checkpoint
    recovered_data = checkpoint_manager.load_checkpoint(checkpoint_id)
    
    if recovered_data:
        print("✓ Checkpoint loaded (with snapshot restoration)")
        
        # Verify files were restored
        all_restored = True
        for filename, expected_content in test_files.items():
            file_path = os.path.join(outputs_dir, filename)
            with open(file_path, 'r') as f:
                actual_content = f.read()
            if actual_content != expected_content:
                print(f"❌ Restoration failed for {filename}")
                all_restored = False
        
        if all_restored:
            print("✓ All files successfully restored from snapshot")
        else:
            return False
    else:
        print("❌ Failed to load checkpoint")
        return False
    
    return True


def test_resumption_behavior():
    """Test the actual resumption behavior from main.py."""
    print("\n=== Testing Resumption Behavior ===")
    
    # Check if there are existing checkpoints to resume from
    default_checkpoint_manager = CheckpointManager()
    checkpoints = default_checkpoint_manager.list_checkpoints()
    
    if checkpoints:
        latest_checkpoint = checkpoints[0]  # Already sorted newest first
        print(f"✓ Found {len(checkpoints)} existing checkpoints")
        print(f"  Latest: {latest_checkpoint['checkpoint_id']}")
        print(f"  Phase: {latest_checkpoint['phase']} → {latest_checkpoint['step']}")
        print(f"  Timestamp: {latest_checkpoint['timestamp']}")
        
        # Test loading the latest checkpoint
        recovered_session_state = default_checkpoint_manager.load_checkpoint(
            return_session_state=True
        )
        
        if isinstance(recovered_session_state, SessionState):
            print("✓ Successfully recovered latest checkpoint as SessionState")
            print(f"  Current phase: {recovered_session_state.current_phase}")
            print(f"  Current task: {recovered_session_state.current_task}")
            print(f"  Task file path: {recovered_session_state.task_file_path}")
            return True
        else:
            print("❌ Failed to recover as SessionState")
            return False
    else:
        print("ℹ️  No existing checkpoints found (fresh start)")
        return True


def main():
    """Run comprehensive checkpoint tests."""
    print("🔄 Comprehensive Checkpoint System Testing")
    print("=" * 50)
    
    tests = [
        ("Basic Checkpoint Creation/Recovery", test_checkpoint_creation_and_recovery),
        ("Legacy Dict Checkpoint Recovery", test_legacy_dict_checkpoint_recovery),
        ("Checkpoint Listing and Cleanup", test_checkpoint_listing_and_cleanup),
        ("Output Snapshots", test_output_snapshots),
        ("Resumption Behavior", test_resumption_behavior),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            print(f"\n🧪 Running: {test_name}")
            result = test_func()
            results.append((test_name, result))
            print(f"{'✅ PASSED' if result else '❌ FAILED'}: {test_name}")
        except Exception as e:
            print(f"❌ ERROR in {test_name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"📊 Test Results: {passed}/{total} passed")
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    if passed == total:
        print("\n🎉 ALL CHECKPOINT TESTS PASSED!")
        print("✅ Checkpoint system is fully functional")
        print("✅ SessionState integration working")  
        print("✅ Legacy compatibility maintained")
        print("✅ Output snapshots and recovery working")
        print("✅ Ready for production use")
    else:
        print(f"\n⚠️  {total - passed} TESTS FAILED!")
        print("❌ Checkpoint system needs attention")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)