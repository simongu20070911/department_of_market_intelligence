# /department_of_market_intelligence/utils/tool_factory.py
"""
Centralized tool factory for creating execution-mode-aware tools.
"""

import os
from typing import List, Any
from .. import config


def create_agent_tools(agent_name: str = "Unknown") -> List[Any]:
    """Create tools for an agent based on the current execution mode.
    
    Args:
        agent_name: Name of the agent requesting tools
        
    Returns:
        List of tools appropriate for the current execution mode
    """
    if config.EXECUTION_MODE == "dry_run":
        return _create_mock_tools(agent_name)
    elif config.EXECUTION_MODE == "sandbox":
        return _create_sandbox_tools(agent_name)
    elif config.EXECUTION_MODE == "production":
        return _create_production_tools(agent_name)
    else:
        raise ValueError(f"Unknown execution mode: {config.EXECUTION_MODE}")


def _create_mock_tools(agent_name: str) -> List[Any]:
    """Create mock tools for dry run mode.
    
    Args:
        agent_name: Name of the agent
        
    Returns:
        List of mock tools
    """
    print(f"🎭 Creating mock tools for {agent_name} (dry_run mode)")
    
    if config.DRY_RUN_SKIP_LLM:
        from ..tools.mock_llm_agent import create_mock_llm_agent
        return []  # Mock LLM agents don't need tools
    else:
        from ..tools.mock_tools import mock_desktop_commander_toolset
        return mock_desktop_commander_toolset


def _create_sandbox_tools(agent_name: str) -> List[Any]:
    """Create sandbox-aware tools that output to real project directories.
    
    Sandbox mode provides safety through execution monitoring and logging,
    but outputs go to the real project directories for actual use.
    
    Args:
        agent_name: Name of the agent
        
    Returns:
        List of MCP tools configured for project directory access
    """
    print(f"🏗️  Creating sandbox tools for {agent_name}")
    
    try:
        from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioConnectionParams
        from mcp.client.stdio import StdioServerParameters
        
        # Use project root directory for real output generation
        # Sandbox mode provides safety through monitoring, not directory isolation
        toolset = MCPToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command=config.DESKTOP_COMMANDER_COMMAND,
                    args=config.DESKTOP_COMMANDER_ARGS,
                    cwd=config._BASE_DIR,  # Use project root for real outputs
                    env={
                        **os.environ,
                        # Add sandbox mode indicators
                        "DOMI_EXECUTION_MODE": "sandbox",
                        "DOMI_SAFETY_MODE": "true",
                        # Configure Desktop Commander limits for larger files
                        "DC_FILE_WRITE_LINE_LIMIT": "10000",
                        "DC_FILE_READ_LINE_LIMIT": "15000"
                    }
                ),
                timeout=config.MCP_TIMEOUT_SECONDS
            )
        )
        
        print(f"✅ Sandbox MCP toolset created for {agent_name}")
        print(f"   📁 Working directory: {config._BASE_DIR}")
        print(f"   📊 Outputs directory: {config.get_outputs_dir()}")
        print(f"   🔒 Safety: Execution monitoring enabled")
        
        return [toolset]
        
    except Exception as e:
        print(f"❌ Failed to create sandbox tools for {agent_name}: {e}")
        print("🔄 Falling back to mock tools")
        return _create_mock_tools(agent_name)


def _create_production_tools(agent_name: str) -> List[Any]:
    """Create production tools with safety checks.
    
    Args:
        agent_name: Name of the agent
        
    Returns:
        List of production tools
    """
    # Safety check for production mode
    if config.REQUIRE_PRODUCTION_CONFIRMATION:
        print(f"⚠️  PRODUCTION MODE: Creating real tools for {agent_name}")
        print("   This will create actual files and make real changes!")
        
        if not os.getenv("DOMI_PRODUCTION_CONFIRMED"):
            response = input("🚨 Continue with production mode? (type 'CONFIRM'): ")
            if response != "CONFIRM":
                print("❌ Production mode cancelled, using sandbox tools instead")
                return _create_sandbox_tools(agent_name)
            
            # Set environment variable to avoid repeated prompts
            os.environ["DOMI_PRODUCTION_CONFIRMED"] = "true"
    
    print(f"🚨 Creating PRODUCTION tools for {agent_name}")
    
    try:
        import concurrent.futures
        from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioConnectionParams
        from mcp.client.stdio import StdioServerParameters
        
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        def create_mcp_toolset():
            return MCPToolset(
                connection_params=StdioConnectionParams(
                    server_params=StdioServerParameters(
                        command=config.DESKTOP_COMMANDER_COMMAND,
                        args=config.DESKTOP_COMMANDER_ARGS,
                        cwd=project_root,
                        env={
                            **os.environ,
                            # Configure Desktop Commander limits for larger files
                            "DC_FILE_WRITE_LINE_LIMIT": "10000",
                            "DC_FILE_READ_LINE_LIMIT": "15000",
                            # Production mode indicators
                            "DOMI_EXECUTION_MODE": "production"
                        }
                    ),
                    timeout=config.MCP_TIMEOUT_SECONDS
                )
            )
        
        # Use ThreadPoolExecutor with extended timeout
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(create_mcp_toolset)
            toolset = future.result(timeout=config.MCP_TIMEOUT_SECONDS + 10)
            tools = [toolset]
            print(f"✅ Production MCP toolset created for {agent_name}")
            return tools
            
    except Exception as e:
        print(f"❌ Failed to create production tools for {agent_name}: {e}")
        print("🔄 Falling back to sandbox tools for safety")
        return _create_sandbox_tools(agent_name)


def get_execution_mode_info() -> dict:
    """Get information about the current execution mode.
    
    Returns:
        Dictionary with execution mode information
    """
    info = {
        "mode": config.EXECUTION_MODE,
        "description": "",
        "safety_level": "",
        "file_operations": ""
    }
    
    if config.EXECUTION_MODE == "dry_run":
        info.update({
            "description": "Mock tools only, no real operations",
            "safety_level": "SAFE",
            "file_operations": "Simulated only"
        })
    elif config.EXECUTION_MODE == "sandbox":
        info.update({
            "description": "Real tools with project directory access",
            "safety_level": "SAFE", 
            "file_operations": f"Real outputs to {config.get_outputs_dir()}"
        })
    elif config.EXECUTION_MODE == "production":
        info.update({
            "description": "Real tools with actual file operations",
            "safety_level": "DANGEROUS",
            "file_operations": "REAL - affects actual files"
        })
    
    return info


def print_execution_mode_warning():
    """Print a warning about the current execution mode."""
    info = get_execution_mode_info()
    
    print(f"\n🔧 EXECUTION MODE: {info['mode'].upper()}")
    print(f"   📋 {info['description']}")
    print(f"   🛡️  Safety: {info['safety_level']}")
    print(f"   📁 Files: {info['file_operations']}")
    
    if config.EXECUTION_MODE == "production":
        print("   🚨 WARNING: This mode creates real files and makes actual changes!")
    elif config.EXECUTION_MODE == "sandbox":
        print(f"   📊 Outputs: {config.get_outputs_dir()}")
    
    print()


def validate_execution_mode() -> bool:
    """Validate the current execution mode configuration.
    
    Returns:
        True if configuration is valid
    """
    valid_modes = ["dry_run", "sandbox", "production"]
    
    if config.EXECUTION_MODE not in valid_modes:
        print(f"❌ Invalid execution mode: {config.EXECUTION_MODE}")
        print(f"   Valid modes: {', '.join(valid_modes)}")
        return False
    
    if config.EXECUTION_MODE == "sandbox":
        from .sandbox_manager import validate_sandbox_safety
        if not validate_sandbox_safety():
            print("❌ Sandbox configuration is not safe")
            return False
    
    return True


if __name__ == "__main__":
    # CLI interface for testing tool creation
    import sys
    
    if len(sys.argv) < 2:
        print("Tool Factory Test")
        print("Usage: python -m utils.tool_factory <agent_name>")
        sys.exit(1)
    
    agent_name = sys.argv[1]
    
    print_execution_mode_warning()
    
    if not validate_execution_mode():
        print("❌ Invalid execution mode configuration")
        sys.exit(1)
    
    tools = create_agent_tools(agent_name)
    print(f"✅ Created {len(tools)} tools for {agent_name}")
    
    info = get_execution_mode_info()
    print(f"🔧 Mode: {info['mode']} ({info['safety_level']})")