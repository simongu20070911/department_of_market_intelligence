#!/usr/bin/env python3
"""Test script with dry run mode enabled to catch bugs early."""

import sys
import os

# Enable dry run mode before importing the module
os.environ['DRY_RUN_MODE'] = 'True'

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Temporarily modify config
import department_of_market_intelligence.config as config
config.DRY_RUN_MODE = True
config.MAX_DRY_RUN_ITERATIONS = 1  # Just one iteration to test
config.VERBOSE_LOGGING = False

# Now run main
from department_of_market_intelligence.main import main
import asyncio

if __name__ == "__main__":
    print("=== DRY RUN TEST ===")
    print("Testing system with limited iterations to catch bugs early...")
    print("-" * 60)
    
    try:
        asyncio.run(main())
        print("\n✅ Dry run completed successfully!")
    except Exception as e:
        print(f"\n❌ Error during dry run: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)