# /department_of_market_intelligence/main.py
import sys
import asyncio
import os
import warnings
import logging
import litellm

from .utils.logger import get_logger, apply_output_filtering

# Apply output filtering early
apply_output_filtering()

# Suppress MCP and asyncio cleanup warnings
warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*cancel scope.*")
warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*stdio_client.*")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="mcp.*")
warnings.filterwarnings("ignore", category=UserWarning, module="anyio.*")
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService
from google.genai.types import Content, Part
from .workflows.root_workflow_context_aware import RootWorkflowAgentContextAware
from . import config
from .config import TASKS_DIR, VERBOSE_LOGGING
from .utils.task_loader import load_task_description, validate_task_id, get_task_file_path, create_task_loading_summary
from .utils.state_model import DOMISessionState

logger = get_logger(__name__)

# Suppress warnings
warnings.filterwarnings("ignore")
logging.getLogger("google.adk.tools.mcp_tool").setLevel(logging.ERROR)

# Configure logging based on config
if VERBOSE_LOGGING:
    os.environ['LITELLM_LOG'] = 'DEBUG'
else:
    os.environ['LITELLM_LOG'] = 'ERROR'

# Configure LiteLLM retries for ALL errors
os.environ['LITELLM_NUM_RETRIES'] = '3'  # Retry up to 3 times
os.environ['LITELLM_RETRY_STRATEGY'] = 'exponential_backoff'
# Remove status code restriction - retry on ALL errors
# os.environ['LITELLM_RETRY_ON_STATUS_CODES'] = '429,500,502,503,504'

async def initialize_toolset():
    """Initialize the MCP toolset and register it globally."""
    from .tools.toolset_registry import toolset_registry
    from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioConnectionParams
    from mcp.client.stdio import StdioServerParameters
    
    logger.info("🔧 Initializing MCP toolset...")
    
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    toolset = MCPToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command=config.DESKTOP_COMMANDER_COMMAND,
                args=config.DESKTOP_COMMANDER_ARGS,
                cwd=project_root
            ),
            timeout=config.MCP_TIMEOUT_SECONDS
        )
    )
    
    toolset_registry.set_desktop_commander_toolset(toolset)
    logger.info("✅ Successfully initialized MCP toolset.")


async def main(resume: bool = True):
    """Main function to orchestrate the research process.
    
    Args:
        resume: If True, resumes from the latest checkpoint.
    """
    from .utils.checkpoint_manager import checkpoint_manager
    
    session_service = InMemorySessionService()
    artifact_service = InMemoryArtifactService()

    # Enhanced resume logic
    if resume and checkpoint_manager.has_snapshot():
        logger.info("🔄 Resuming from the latest snapshot...")
        initial_state = checkpoint_manager.load_latest_snapshot()
        if initial_state:
            logger.info(f"📋 Resumed Task ID: {initial_state.task_id}")
            logger.info(f"🎯 Resumed Phase: {initial_state.current_phase}")
        else:
            logger.error("❌ Failed to load snapshot, starting fresh.")
            initial_state = None
    else:
        logger.info(f"🚀 Starting new task: {config.TASK_ID}")
        initial_state = None

    await initialize_toolset()

    logger.info("🔍 Using context-aware validation system")
    root_agent = RootWorkflowAgentContextAware(name="MarketAlpha_Root")

    runner = Runner(
        agent=root_agent,
        app_name="ULTRATHINK_QUANTITATIVE",
        session_service=session_service,
        artifact_service=artifact_service,
    )

    if initial_state is None:
        if not validate_task_id(config.TASK_ID):
            logger.error(f"❌ ERROR: Task '{config.TASK_ID}' not found!")
            logger.error("\n" + create_task_loading_summary())
            return
        
        task_file_path = get_task_file_path(config.TASK_ID)
        logger.info(f"📋 Task Configuration:")
        logger.info(f"   • Task ID: {config.TASK_ID}")
        logger.info(f"   • Task File: {task_file_path}")
        logger.info(f"   • Tasks Directory: {TASKS_DIR}")
        
        try:
            task_content = load_task_description(config.TASK_ID)
            logger.info(f"   • Task Content: {len(task_content)} characters, {task_content.count(chr(10)) + 1} lines")
        except Exception as e:
            logger.error(f"❌ ERROR: Failed to load task '{config.TASK_ID}': {e}")
            return
        
        initial_state = DOMISessionState(
            task_id=config.TASK_ID,
            metadata={"task_file_path": task_file_path}
        )
        logger.info(f"--- Starting Research Task from {task_file_path} ---")
    else:
        logger.info(f"--- Resuming Research Task: {initial_state.metadata.get('task_file_path', 'Unknown')} ---")
    
    session = await session_service.create_session(
        app_name="ULTRATHINK_QUANTITATIVE",
        user_id="quant_team",
        state=initial_state.dict()
    )
    
    start_message = Content(parts=[Part(text="Begin the research process.")])
    
    try:
        async for event in runner.run_async(
            session_id=session.id,
            user_id=session.user_id,
            new_message=start_message
        ):
            if config.STREAMING_ENABLED:
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            if event.partial:
                                sys.stdout.write(part.text)
                                sys.stdout.flush()
                            else:
                                logger.info(f"\n[{event.author}]: {part.text.strip()}")
                        if part.function_call:
                            logger.info(f"[{event.author}]: TOOL CALL: {part.function_call.name}")
            else:
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            logger.info(f"[{event.author}]: {part.text.strip()}")
                        if part.function_call:
                            logger.info(f"[{event.author}]: TOOL CALL: {part.function_call.name}")
    except (Exception, BaseExceptionGroup) as e:
        if "stdio_client" in str(e) or "cancel scope" in str(e):
            logger.warning(f"\n⚠️  MCP connection cleanup (non-fatal)")
        else:
            logger.error(f"\n❌ Workflow execution error: {e}", exc_info=True)
        
        try:
            from .tools.toolset_registry import toolset_registry
            toolset_registry.cleanup()
        except Exception:
            pass
    finally:
        logger.info("\n🔚 Research task completed.")

def parse_arguments():
    """Parse command line arguments."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Department of Market Intelligence (DoMI) - Agentic Research Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Execution Modes:
  sandbox     Real tools with project directory access (safe with real outputs)
  production  Real tools with full system access (use with caution)

Examples:
  %(prog)s --mode sandbox      # Test with real tools safely
  %(prog)s --mode production   # Run with real file operations
  %(prog)s --task my_research  # Specify task ID
        """
    )
    
    parser.add_argument(
        '--task', '--task-id',
        default=None,
        help='Task ID to run (overrides TASK_ID env var)'
    )
    
    parser.add_argument(
        '--resume',
        action='store_true',
        default=True,
        help='Resume from checkpoint (default: True, use --no-resume to disable)'
    )
    
    parser.add_argument(
        '--no-resume',
        action='store_false',
        dest='resume',
        help='Disable automatic resume from checkpoint'
    )
    
    parser.add_argument(
        '--sandbox-dir',
        default=None,
        help='Custom sandbox directory'
    )
    
    parser.add_argument(
        '--no-cleanup',
        action='store_true', 
        help='Disable automatic sandbox cleanup'
    )
    
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Validate configuration and exit'
    )
    
    return parser.parse_args()


def apply_cli_overrides(args):
    """Apply CLI argument overrides to configuration."""
    import os
    from . import config
    
    if args.task:
        config.TASK_ID = args.task
        os.environ["TASK_ID"] = args.task
        logger.info(f"📋 Task ID set to: {args.task}")
    
    if args.sandbox_dir:
        config.SANDBOX_BASE_DIR = args.sandbox_dir
        os.environ["SANDBOX_BASE_DIR"] = args.sandbox_dir
        logger.info(f"📁 Sandbox directory set to: {args.sandbox_dir}")
    
    if args.no_cleanup:
        config.AUTO_CLEANUP_SANDBOX = False
        os.environ["AUTO_CLEANUP_SANDBOX"] = "false"
        logger.info("🚫 Sandbox auto-cleanup disabled")


def validate_configuration():
    """Validate system configuration before starting."""
    from . import config
    from .utils.checkpoint_manager import CheckpointManager
    import shutil
    
    logger.info("🔍 VALIDATING CONFIGURATION")
    logger.info("="*50)
    
    checkpoint_manager = CheckpointManager(config.TASK_ID)

    task_file = os.path.join(config.TASKS_DIR, f"{config.TASK_ID}.md")
    if not os.path.exists(task_file):
        logger.error(f"❌ Task file not found: {task_file}")
        return False
    else:
        logger.info(f"✅ Task file found: {config.TASK_ID}.md")
        
    if config.CLEAR_OUTPUTS_ON_START and not checkpoint_manager.has_snapshot():
        outputs_dir = config.get_outputs_dir(config.TASK_ID)
        if os.path.exists(outputs_dir):
            shutil.rmtree(outputs_dir)
            logger.info(f"🗑️ Cleared outputs directory: {outputs_dir}")
        os.makedirs(outputs_dir, exist_ok=True)

    logger.info("✅ Configuration validation passed")
    return True


async def main_with_args():
    """Main function with CLI argument support."""
    args = parse_arguments()
    
    apply_cli_overrides(args)
    
    if not validate_configuration():
        sys.exit(1)
    
    if args.validate_only:
        logger.info("✅ Validation complete")
        return
    
    await main(resume=args.resume)


if __name__ == "__main__":
    import asyncio
    import os
    
    asyncio.run(main_with_args())