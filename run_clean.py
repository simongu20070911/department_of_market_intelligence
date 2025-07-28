#!/usr/bin/env python3
"""
Clean runner for the Market Intelligence system with minimal output.
Suppresses verbose logging and MCP authentication warnings.
"""

import warnings
import sys
import os
import asyncio

# Suppress all warnings
warnings.filterwarnings("ignore")

# Set environment variables to reduce verbosity
os.environ['LITELLM_LOG'] = 'ERROR'
os.environ['GRPC_VERBOSITY'] = 'ERROR'

# Now import and run the main module
from department_of_market_intelligence.main import main

if __name__ == "__main__":
    print("=== ULTRATHINK_QUANTITATIVE Market Intelligence System ===")
    print("Starting research process...")
    print("-" * 60)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user.")
    except Exception as e:
        print(f"\nError: {e}")