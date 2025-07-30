#!/usr/bin/env python3
"""
Debug script to capture exactly what tool schema ADK is sending to the LLM endpoint.
"""

import json
import asyncio
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioConnectionParams
from mcp.client.stdio import StdioServerParameters
import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from department_of_market_intelligence import config

async def debug_mcp_tool_schema():
    """Debug what tool schema MCP Desktop Commander generates."""
    print("🔍 Creating MCP Desktop Commander toolset...")
    
    # Create MCP toolset exactly like in the real system
    toolset = MCPToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command=config.DESKTOP_COMMANDER_COMMAND,
                args=config.DESKTOP_COMMANDER_ARGS,
                cwd=project_root
            )
        )
    )
    
    print("✅ MCP toolset created")
    
    # Wait for tools to be loaded
    await asyncio.sleep(3)
    
    print("🔍 Getting tool definitions...")
    
    # Try to get tools using get_tools method
    try:
        print("🔍 Getting tools using get_tools() method...")
        tools = await toolset.get_tools()
        
        if tools:
            print(f"📋 Found {len(tools)} tools:")
            for i, tool in enumerate(tools[:3]):  # Show first 3 tools
                print(f"  {i+1}. {tool.name}")
                print(f"     Description: {getattr(tool, 'description', 'No description')}")
                
                # Print tool schema/function definition
                print("     Checking for schema methods...")
                
                # Try process_llm_request to see if it generates a schema
                if hasattr(tool, 'process_llm_request'):
                    print("     ✅ Has process_llm_request method")
                
                # Check all attributes that might contain schema info  
                schema_found = False
                for attr_name in ['get_function_schema', 'function_schema', 'schema', '_schema', 'input_schema']:
                    if hasattr(tool, attr_name):
                        try:
                            attr_value = getattr(tool, attr_name)
                            if callable(attr_value):
                                schema = attr_value()
                                print(f"     Schema from {attr_name}(): {json.dumps(schema, indent=2)}")
                                schema_found = True
                                break
                            else:
                                print(f"     Schema from {attr_name}: {json.dumps(attr_value, indent=2)}")
                                schema_found = True
                                break
                        except Exception as e:
                            print(f"     Error getting {attr_name}: {e}")
                
                if not schema_found:
                    print("     ❌ No schema found in any standard locations")
                    # Print ALL attributes for debugging
                    all_attrs = [attr for attr in dir(tool) if not attr.startswith('__')]
                    print(f"     All attributes: {all_attrs}")
                
                print()  # Empty line for readability
            
            if len(tools) > 3:
                print(f"     ... and {len(tools) - 3} more tools")
        else:
            print("❌ No tools returned from get_tools()")
            
    except Exception as e:
        print(f"❌ Error getting tools: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_mcp_tool_schema())