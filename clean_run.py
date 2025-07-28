#!/usr/bin/env python3
"""Clean runner that suppresses MCP authentication warnings."""

import sys
import os
import warnings
import logging

# Suppress all warnings
warnings.filterwarnings("ignore")

# Suppress specific logging
logging.getLogger("google.adk.tools.mcp_tool").setLevel(logging.ERROR)

# Set environment variables
os.environ['LITELLM_LOG'] = 'ERROR'
os.environ['GRPC_VERBOSITY'] = 'ERROR'

# Create a custom output filter
class CleanOutput:
    def __init__(self, stream):
        self.stream = stream
        self.buffer = ""
        
    def write(self, text):
        # Filter out unwanted messages
        lines = (self.buffer + text).split('\n')
        self.buffer = lines[-1]  # Keep incomplete line
        
        for line in lines[:-1]:
            if not any(skip in line for skip in [
                "auth_config or auth_config.auth_scheme is missing",
                "Will skip authentication.Using FunctionTool",
                "UserWarning: [EXPERIMENTAL]",
                "Generating tools list",
                "Loading server.ts",
                "Setting up request handlers",
                "Initialized FilteredStdioServerTransport",
                "Loading configuration",
                "Configuration loaded successfully",
                "Connecting server",
                "Server connected successfully",
                "super().__init__",
            ]):
                self.stream.write(line + '\n')
                self.stream.flush()
    
    def flush(self):
        if self.buffer:
            self.stream.write(self.buffer)
            self.buffer = ""
        self.stream.flush()
        
    def __getattr__(self, name):
        return getattr(self.stream, name)

# Replace stdout and stderr with filtered versions
sys.stdout = CleanOutput(sys.stdout)
sys.stderr = CleanOutput(sys.stderr)

# Now run the main module
if __name__ == "__main__":
    from department_of_market_intelligence.main import main
    import asyncio
    
    print("=== ULTRATHINK_QUANTITATIVE Market Intelligence System ===")
    print("Starting research process...")
    print("-" * 60)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user.")
    except Exception as e:
        print(f"\nError: {e}")
        raise