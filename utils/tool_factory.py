# /department_of_market_intelligence/utils/tool_factory.py
"""
Centralized tool factory for creating execution-mode-aware tools.
"""

import os
from typing import List, Any
from .. import config
from .logger import get_logger

logger = get_logger(__name__)


def create_agent_tools(agent_name: str = "Unknown") -> List[Any]:
    """Create tools for an agent based on the current execution mode.
    
    Args:
        agent_name: Name of the agent requesting tools
        
    Returns:
        List of tools appropriate for the current execution mode
    """
    if config.EXECUTION_MODE == "sandbox":
        return _create_sandbox_tools(agent_name)
    elif config.EXECUTION_MODE == "production":
        return _create_production_tools(agent_name)
    else:
        logger.warning(f"⚠️ Unknown execution mode '{config.EXECUTION_MODE}', defaulting to sandbox.")
        return _create_sandbox_tools(agent_name)


def _create_sandbox_tools(agent_name: str) -> List[Any]:
    """Create sandbox-aware tools that output to real project directories.
    
    Sandbox mode provides safety through execution monitoring and logging,
    but outputs go to the real project directories for actual use.
    
    Args:
        agent_name: Name of the agent
        
    Returns:
        List of MCP tools configured for project directory access
    """
    logger.info(f"🏗️  Creating sandbox tools for {agent_name}")
    
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
                        "DOMI_SAFETY_MODE": "true"
                    }
                ),
                timeout=config.MCP_TIMEOUT_SECONDS
            )
        )
        
        
        logger.info(f"✅ Sandbox MCP toolset created for {agent_name}")
        logger.info(f"   📁 Working directory: {config._BASE_DIR}")
        logger.info(f"   📊 Outputs directory: {config.get_outputs_dir()}")
        logger.info(f"   🔒 Safety: Execution monitoring enabled")
        
        return [toolset]
        
    except Exception as e:
        logger.error(f"❌ Failed to create sandbox tools for {agent_name}: {e}")
        logger.error("❌ Cannot fall back to mock tools as they are removed.")
        raise e


def _create_production_tools(agent_name: str) -> List[Any]:
    """Create production tools with safety checks.
    
    Args:
        agent_name: Name of the agent
        
    Returns:
        List of production tools
    """
    # Safety check for production mode
    if config.REQUIRE_PRODUCTION_CONFIRMATION:
        logger.warning(f"⚠️  PRODUCTION MODE: Creating real tools for {agent_name}")
        logger.warning("   This will create actual files and make real changes!")
        
        if not os.getenv("DOMI_PRODUCTION_CONFIRMED"):
            response = input("🚨 Continue with production mode? (type 'CONFIRM'): ")
            if response != "CONFIRM":
                logger.error("❌ Production mode cancelled, using sandbox tools instead")
                return _create_sandbox_tools(agent_name)
            
            # Set environment variable to avoid repeated prompts
            os.environ["DOMI_PRODUCTION_CONFIRMED"] = "true"
    
    logger.info(f"🚨 Creating PRODUCTION tools for {agent_name}")
    
    try:
        import concurrent.futures
        from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioConnectionParams
        from mcp.client.stdio import StdioServerParameters
        
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        def create_mcp_toolset():
            toolset = MCPToolset(
                connection_params=StdioConnectionParams(
                    server_params=StdioServerParameters(
                        command=config.DESKTOP_COMMANDER_COMMAND,
                        args=config.DESKTOP_COMMANDER_ARGS,
                        cwd=project_root,
                        env={
                            **os.environ,
                            # Production mode indicators  
                            "DOMI_EXECUTION_MODE": "production"
                        }
                    ),
                    timeout=config.MCP_TIMEOUT_SECONDS
                )
            )
            
            
            return toolset
        
        # Use ThreadPoolExecutor with extended timeout
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(create_mcp_toolset)
            toolset = future.result(timeout=config.MCP_TIMEOUT_SECONDS + 10)
            tools = [toolset]
            logger.info(f"✅ Production MCP toolset created for {agent_name}")
            return tools
            
    except Exception as e:
        logger.error(f"❌ Failed to create production tools for {agent_name}: {e}")
        logger.warning("🔄 Falling back to sandbox tools for safety")
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
    
    if config.EXECUTION_MODE == "sandbox":
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
    
    logger.info(f"\n🔧 EXECUTION MODE: {info['mode'].upper()}")
    logger.info(f"   📋 {info['description']}")
    logger.info(f"   🛡️  Safety: {info['safety_level']}")
    logger.info(f"   📁 Files: {info['file_operations']}")
    
    if config.EXECUTION_MODE == "production":
        logger.warning("   🚨 WARNING: This mode creates real files and makes actual changes!")
    elif config.EXECUTION_MODE == "sandbox":
        logger.info(f"   📊 Outputs: {config.get_outputs_dir()}")
    
    logger.info("")


def validate_execution_mode() -> bool:
    """Validate the current execution mode configuration.
    
    Returns:
        True if configuration is valid
    """
    valid_modes = ["sandbox", "production"]
    
    if config.EXECUTION_MODE not in valid_modes:
        logger.error(f"❌ Invalid execution mode: {config.EXECUTION_MODE}")
        logger.error(f"   Valid modes: {', '.join(valid_modes)}")
        return False
    
    if config.EXECUTION_MODE == "sandbox":
        from .sandbox_manager import validate_sandbox_safety
        if not validate_sandbox_safety():
            logger.error("❌ Sandbox configuration is not safe")
            return False
    
    return True


if __name__ == "__main__":
    # CLI interface for testing tool creation
    import sys
    
    if len(sys.argv) < 2:
        logger.info("Tool Factory Test")
        logger.info("Usage: python -m utils.tool_factory <agent_name>")
        sys.exit(1)
    
    agent_name = sys.argv[1]
    
    print_execution_mode_warning()
    
    if not validate_execution_mode():
        logger.error("❌ Invalid execution mode configuration")
        sys.exit(1)
    
    tools = create_agent_tools(agent_name)
    logger.info(f"✅ Created {len(tools)} tools for {agent_name}")
    
    info = get_execution_mode_info()
    logger.info(f"🔧 Mode: {info['mode']} ({info['safety_level']})")