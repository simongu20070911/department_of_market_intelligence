#!/usr/bin/env python3
"""Test checkpointing system functionality."""

import sys
import os
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup test environment
import department_of_market_intelligence.config as config

# Use a temporary task ID for testing
TEST_TASK_ID = "test_checkpointing_task"
config.TASK_ID = TEST_TASK_ID
config.ENABLE_CHECKPOINTING = True
config.CHECKPOINT_INTERVAL = 1
config.DRY_RUN_MODE = True
config.DRY_RUN_SKIP_LLM = True
config.MAX_DRY_RUN_ITERATIONS = 1
config.VERBOSE_LOGGING = False

# Update directories for test
config.OUTPUTS_DIR = config.get_outputs_dir(TEST_TASK_ID)
config.CHECKPOINTS_DIR = config.get_checkpoints_dir(TEST_TASK_ID)

from department_of_market_intelligence.utils.checkpoint_manager import CheckpointManager
import asyncio


def test_checkpoint_manager():
    """Test basic checkpoint manager functionality."""
    print("🧪 TESTING CHECKPOINT MANAGER")
    print("=" * 50)
    
    # Create a test checkpoint manager
    checkpoint_manager = CheckpointManager(TEST_TASK_ID)
    
    # Test 1: Create checkpoint
    print("\n📝 Test 1: Creating checkpoint...")
    test_state = {
        "current_task": "test_task",
        "phase": "testing",
        "test_data": "sample_value"
    }
    
    checkpoint_id = checkpoint_manager.create_checkpoint(
        phase="testing",
        step="test_step",
        session_state=test_state,
        metadata={"test": True}
    )
    
    assert checkpoint_id is not None, "Checkpoint creation failed"
    print(f"✅ Checkpoint created: {checkpoint_id}")
    
    # Test 2: List checkpoints
    print("\n📋 Test 2: Listing checkpoints...")
    checkpoints = checkpoint_manager.list_checkpoints()
    assert len(checkpoints) >= 1, "No checkpoints found"
    print(f"✅ Found {len(checkpoints)} checkpoint(s)")
    
    # Test 3: Load checkpoint
    print("\n🔄 Test 3: Loading checkpoint...")
    loaded_data = checkpoint_manager.load_checkpoint(checkpoint_id)
    assert loaded_data is not None, "Checkpoint loading failed"
    assert loaded_data['session_state']['current_task'] == "test_task", "Session state not preserved"
    print("✅ Checkpoint loaded successfully")
    
    # Test 4: Recovery info
    print("\n🔍 Test 4: Getting recovery info...")
    recovery_info = checkpoint_manager.get_recovery_info()
    assert recovery_info['can_resume'] == True, "Recovery info incorrect"
    assert recovery_info['task_id'] == TEST_TASK_ID, "Task ID mismatch"
    print("✅ Recovery info correct")
    
    # Test 5: Create multiple checkpoints
    print("\n📝 Test 5: Creating multiple checkpoints...")
    for i in range(3):
        checkpoint_manager.create_checkpoint(
            phase="testing",
            step=f"step_{i+2}",
            session_state={"step": i+2},
            metadata={"sequence": i+2}
        )
    
    checkpoints = checkpoint_manager.list_checkpoints()
    assert len(checkpoints) >= 4, f"Expected at least 4 checkpoints, got {len(checkpoints)}"
    print(f"✅ Created multiple checkpoints, total: {len(checkpoints)}")
    
    # Test 6: Cleanup
    print("\n🧹 Test 6: Testing cleanup...")
    checkpoint_manager.cleanup_old_checkpoints(keep_count=2)
    checkpoints_after_cleanup = checkpoint_manager.list_checkpoints()
    assert len(checkpoints_after_cleanup) <= 2, f"Cleanup failed, still have {len(checkpoints_after_cleanup)} checkpoints"
    print(f"✅ Cleanup successful, kept {len(checkpoints_after_cleanup)} checkpoints")
    
    print("\n🎉 All checkpoint manager tests passed!")
    return True


async def test_workflow_checkpointing():
    """Test checkpointing integration with workflow."""
    print("\n🧪 TESTING WORKFLOW CHECKPOINTING INTEGRATION")
    print("=" * 60)
    
    # Import here to ensure config is set up
    from department_of_market_intelligence.main import main
    
    try:
        print("🚀 Running workflow with checkpointing enabled...")
        await main()
        print("✅ Workflow completed successfully")
        
        # Check that checkpoints were created
        checkpoint_manager = CheckpointManager(TEST_TASK_ID)
        checkpoints = checkpoint_manager.list_checkpoints()
        
        print(f"📊 Created {len(checkpoints)} checkpoints during workflow execution")
        
        if len(checkpoints) > 0:
            print("📋 Checkpoint phases created:")
            phases_seen = set()
            for cp in checkpoints:
                phase_step = f"{cp['phase']} → {cp['step']}"
                if phase_step not in phases_seen:
                    print(f"   - {phase_step}")
                    phases_seen.add(phase_step)
            
            print("✅ Workflow checkpointing integration successful")
            return True
        else:
            print("❌ No checkpoints created during workflow execution")
            return False
            
    except Exception as e:
        print(f"❌ Workflow execution failed: {e}")
        return False


def cleanup_test_data():
    """Clean up test directories."""
    print("\n🧹 Cleaning up test data...")
    
    test_outputs = config.get_outputs_dir(TEST_TASK_ID)
    test_checkpoints = config.get_checkpoints_dir(TEST_TASK_ID)
    
    for directory in [test_outputs, test_checkpoints]:
        if os.path.exists(directory):
            try:
                shutil.rmtree(directory)
                print(f"   Removed: {directory}")
            except Exception as e:
                print(f"   Warning: Could not remove {directory}: {e}")


async def main():
    """Run all checkpointing tests."""
    print("🧪 TESTING CHECKPOINTING SYSTEM")
    print("Testing comprehensive checkpoint functionality for task recovery")
    print("=" * 80)
    
    try:
        # Test 1: Basic checkpoint manager
        test1_success = test_checkpoint_manager()
        
        # Test 2: Workflow integration
        test2_success = await test_workflow_checkpointing()
        
        # Summary
        print("\n" + "=" * 80)
        print("🎯 TEST SUMMARY")
        print("=" * 80)
        print(f"Checkpoint Manager: {'✅ PASSED' if test1_success else '❌ FAILED'}")
        print(f"Workflow Integration: {'✅ PASSED' if test2_success else '❌ FAILED'}")
        
        overall_success = test1_success and test2_success
        
        if overall_success:
            print("\n🎉 ALL CHECKPOINTING TESTS PASSED!")
            print("✅ System ready for production use with recovery capability")
        else:
            print("\n⚠️  Some checkpointing tests failed")
            print("❌ Review implementation before production use")
        
        return overall_success
        
    finally:
        cleanup_test_data()


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)