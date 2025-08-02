#!/usr/bin/env python3
"""Test script to validate the mock directory structure system."""

import os
import sys

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.mock_tools import (
    create_test_output_directory, 
    compare_with_model_structure,
    reset_dry_run_state,
    get_dry_run_summary
)

def main():
    """Test the mock directory structure system."""
    print("🔬 TESTING MOCK DIRECTORY STRUCTURE SYSTEM")
    print("=" * 60)
    
    try:
        # Step 1: Create test directory structure
        print("\n📋 Step 1: Creating test directory structure...")
        test_task_id = create_test_output_directory()
        
        # Step 2: Compare with model structure
        print("\n📋 Step 2: Comparing with model structure...")
        is_match = compare_with_model_structure()
        
        # Step 3: Show comprehensive summary
        print("\n📋 Step 3: Comprehensive test summary...")
        print(get_dry_run_summary())
        
        # Final result
        print("\n" + "=" * 60)
        if is_match:
            print("✅ SUCCESS: Mock system creates correct directory structure!")
            print("✅ Ready to proceed with fixing the real system.")
        else:
            print("❌ FAILURE: Mock system directory structure needs adjustment.")
            print("❌ Fix issues before proceeding to real system.")
        print("=" * 60)
        
        return is_match
        
    except Exception as e:
        print(f"❌ ERROR during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)