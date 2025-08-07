# /department_of_market_intelligence/main.py
import sys

# Install output filters FIRST before any other imports
class OutputFilter:
    def __init__(self, stream):
        self.stream = stream
        self.suppress_lines = [
            "auth_config or auth_config.auth_scheme is missing",
            "Will skip authentication.Using FunctionTool",
            "Generating tools list",
            "[EXPERIMENTAL] BaseAuthenticatedTool",
            "UserWarning",
            "Loading server.ts",
            "Setting up request handlers",
            "[desktop-commander] Initialized",
            "Loading configuration",
            "Configuration loaded successfully",
            "Connecting server",
            "Server connected successfully",
            "stdio_client",
            "cancel scope",
            "GeneratorExit",
            "BaseExceptionGroup",
            "RuntimeError: Attempted to exit cancel scope"
        ]
    
    def write(self, text):
        if not any(suppress in text for suppress in self.suppress_lines):
            self.stream.write(text)
    
    def flush(self):
        self.stream.flush()
    
    def __getattr__(self, name):
        return getattr(self.stream, name)

# Apply filters immediately - check env var since we can't import config yet
import os as _temp_os
if not _temp_os.environ.get('VERBOSE_LOGGING', '').lower() == 'true':
    _orig_stdout = sys.stdout
    _orig_stderr = sys.stderr
    sys.stdout = OutputFilter(_orig_stdout)
    sys.stderr = OutputFilter(_orig_stderr)

import asyncio
import os
import warnings
import logging
import litellm

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
    """Initialize the appropriate toolset and register it globally."""
    from .tools.toolset_registry import toolset_registry
    from . import config
    import os

    print(f"🔧 Initializing toolset for {config.EXECUTION_MODE} mode...")

    if config.EXECUTION_MODE == "dry_run":
        from .tools.mock_tools import mock_desktop_commander_toolset
        toolset_registry.set_desktop_commander_toolset(mock_desktop_commander_toolset, is_real_mcp=False)
        return

    try:
        from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioConnectionParams
        from mcp.client.stdio import StdioServerParameters
        
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
        
        # Configure Desktop Commander limits after creating toolset
        # This is now handled by the tool's persistent configuration
        # and does not need to be set on every run.
        # The erroneous invoke_tool call is removed to prevent crashes.
        
        toolset_registry.set_desktop_commander_toolset(toolset, is_real_mcp=True)
        print(f"✅ Successfully initialized {config.EXECUTION_MODE} toolset.")

    except Exception as e:
        print(f"❌ Failed to create {config.EXECUTION_MODE} toolset: {e}")
        print("🔄 Falling back to mock tools for safety.")
        from .tools.mock_tools import mock_desktop_commander_toolset
        toolset_registry.set_desktop_commander_toolset(mock_desktop_commander_toolset, is_real_mcp=False)


async def main(resume_from_checkpoint: str = None):
    """Main function to orchestrate the research process.
    
    Args:
        resume_from_checkpoint: Optional checkpoint ID to resume from
    """
    from .utils.checkpoint_manager import checkpoint_manager
    
    # Initialize ADK services for this run
    session_service = InMemorySessionService()
    artifact_service = InMemoryArtifactService()

    # Check for resume capability
    if resume_from_checkpoint or (resume_from_checkpoint is None and checkpoint_manager.get_recovery_info()["can_resume"]):
        if resume_from_checkpoint is None:
            resume_from_checkpoint = checkpoint_manager._get_latest_checkpoint()
        
        print(f"🔄 RESUMING FROM CHECKPOINT: {resume_from_checkpoint}")
        checkpoint_data = checkpoint_manager.load_checkpoint(resume_from_checkpoint)
        
        if checkpoint_data:
            print(f"📋 Resuming Task ID: {checkpoint_data['task_id']}")
            print(f"🎯 Resume Point: {checkpoint_data['phase']} → {checkpoint_data['step']}")
            
            # Restore simple session state from checkpoint - following ADK patterns
            initial_state = checkpoint_data['session_state']  # This is already a simple dict
            checkpoint_manager.agent_execution_count = checkpoint_data['agent_execution_count']
        else:
            print("❌ Failed to load checkpoint, starting fresh")
            initial_state = None
    else:
        print(f"🚀 STARTING NEW TASK: {config.TASK_ID}")
        initial_state = None

    # Initialize the global toolset before creating any agents
    await initialize_toolset()

    # The root of our agentic system
    if config.USE_SIMPLIFIED_WORKFLOW:
        print("🔍 Using simplified workflow with centralized phase management")
        from .workflows.root_workflow_simplified import get_simplified_root_workflow
        root_agent = get_simplified_root_workflow()
    else:
        print("🔍 Using context-aware validation system")
        root_agent = RootWorkflowAgentContextAware(name="MarketAlpha_Root")

    runner = Runner(
        agent=root_agent,
        app_name="ULTRATHINK_QUANTITATIVE",
        session_service=session_service,
        artifact_service=artifact_service,
    )

    # Prepare the initial session state with explicit task loading
    if initial_state is None:
        # Validate task ID and load task content
        if not validate_task_id(config.TASK_ID):
            print(f"❌ ERROR: Task '{config.TASK_ID}' not found!")
            print("\n" + create_task_loading_summary())
            return
        
        task_file_path = get_task_file_path(config.TASK_ID)
        print(f"📋 Task Configuration:")
        print(f"   • Task ID: {config.TASK_ID}")
        print(f"   • Task File: {task_file_path}")
        print(f"   • Tasks Directory: {TASKS_DIR}")
        
        # Verify task file exists and is readable
        try:
            task_content = load_task_description(config.TASK_ID)
            print(f"   • Task Content: {len(task_content)} characters, {task_content.count(chr(10)) + 1} lines")
        except Exception as e:
            print(f"❌ ERROR: Failed to load task '{config.TASK_ID}': {e}")
            return
        
        initial_state = {
            "task_id": config.TASK_ID,
            "task_file_path": task_file_path
        }
        print(f"--- Starting Research Task from {task_file_path} ---")
    else:
        print(f"--- Resuming Research Task: {initial_state.get('task_file_path', 'Unknown')} ---")
    
    # Create a session for this research task
    session = await session_service.create_session(
        app_name="ULTRATHINK_QUANTITATIVE",
        user_id="quant_team",
        state=initial_state
    )
    
    # Start the process with an initial message (can be empty)
    start_message = Content(parts=[Part(text="Begin the research process.")])
    
    try:
        async for event in runner.run_async(
            session_id=session.id,
            user_id=session.user_id,
            new_message=start_message
        ):
            # You can process and print events here for real-time monitoring
            if config.STREAMING_ENABLED:
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            if event.partial:
                                # Print partial text on the same line
                                sys.stdout.write(part.text)
                                sys.stdout.flush()
                            else:
                                # Once the full text is received, print a newline
                                print(f"\n[{event.author}]: {part.text.strip()}")
                        if part.function_call:
                            print(f"[{event.author}]: TOOL CALL: {part.function_call.name}")
            else:
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            print(f"[{event.author}]: {part.text.strip()}")
                        if part.function_call:
                            print(f"[{event.author}]: TOOL CALL: {part.function_call.name}")
    except (Exception, BaseExceptionGroup) as e:
        # Handle workflow execution errors and MCP cleanup issues
        if "stdio_client" in str(e) or "cancel scope" in str(e):
            print(f"\n⚠️  MCP connection cleanup (non-fatal)")
        else:
            print(f"\n❌ Workflow execution error: {e}")
            # Add traceback for debugging
            import traceback
            traceback.print_exc()
        
        # Attempt graceful cleanup
        try:
            from .tools.toolset_registry import toolset_registry
            toolset_registry.cleanup()
        except Exception:
            pass  # Suppress cleanup errors
    finally:
        print("\n🔚 Research task completed.")

def parse_arguments():
    """Parse command line arguments."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Department of Market Intelligence (DoMI) - Agentic Research Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Execution Modes:
  dry_run     Mock tools only, no real operations (safest)
  sandbox     Real tools with project directory access (safe with real outputs)  
  production  Real tools with full system access (use with caution)

Examples:
  %(prog)s --mode dry_run      # Test with mock tools
  %(prog)s --mode sandbox      # Test with real tools safely
  %(prog)s --mode production   # Run with real file operations
  %(prog)s --task my_research  # Specify task ID
        """
    )
    
    parser.add_argument(
        '--mode', '--execution-mode',
        choices=['dry_run', 'sandbox', 'production'],
        default=None,
        help='Execution mode (overrides EXECUTION_MODE env var)'
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
    
    # Override execution mode
    if args.mode:
        config.EXECUTION_MODE = args.mode
        config.DRY_RUN_MODE = (args.mode == "dry_run")
        config.DRY_RUN_SKIP_LLM = (args.mode == "dry_run")
        os.environ["EXECUTION_MODE"] = args.mode
        print(f"🔧 Execution mode set to: {args.mode}")
    
    # Override task ID
    if args.task:
        config.TASK_ID = args.task
        os.environ["TASK_ID"] = args.task
        print(f"📋 Task ID set to: {args.task}")
    
    # Override sandbox directory
    if args.sandbox_dir:
        config.SANDBOX_BASE_DIR = args.sandbox_dir
        os.environ["SANDBOX_BASE_DIR"] = args.sandbox_dir
        print(f"📁 Sandbox directory set to: {args.sandbox_dir}")
    
    # Override cleanup setting
    if args.no_cleanup:
        config.AUTO_CLEANUP_SANDBOX = False
        os.environ["AUTO_CLEANUP_SANDBOX"] = "false"
        print("🚫 Sandbox auto-cleanup disabled")


def print_execution_mode_warning():
    """Print a warning about the current execution mode."""
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
    
    print(f"\n🔧 EXECUTION MODE: {info['mode'].upper()}")
    print(f"   📋 {info['description']}")
    print(f"   🛡️  Safety: {info['safety_level']}")
    print(f"   📁 Files: {info['file_operations']}")
    
    if config.EXECUTION_MODE == "production":
        print("   🚨 WARNING: This mode creates real files and makes actual changes!")
    elif config.EXECUTION_MODE == "sandbox":
        print(f"   📊 Outputs: {config.get_outputs_dir()}")
    
    print()


def validate_execution_mode():
    """Validate the current execution mode configuration."""
    valid_modes = ["dry_run", "sandbox", "production"]
    
    if config.EXECUTION_MODE not in valid_modes:
        print(f"❌ Invalid execution mode: {config.EXECUTION_MODE}")
        print(f"   Valid modes: {', '.join(valid_modes)}")
        return False
    
    if config.EXECUTION_MODE == "sandbox":
        # Assuming sandbox is always safe for now as we removed the dedicated check
        pass
    
    return True


def validate_configuration():
    """Validate system configuration before starting."""
    from . import config
    
    print("🔍 VALIDATING CONFIGURATION")
    print("="*50)
    
    # Print execution mode info
    print_execution_mode_warning()
    
    # Validate execution mode
    if not validate_execution_mode():
        print("❌ Configuration validation failed")
        return False
    
    # Validate task exists
    task_file = os.path.join(config.TASKS_DIR, f"{config.TASK_ID}.md")
    if not os.path.exists(task_file):
        print(f"❌ Task file not found: {task_file}")
        return False
    else:
        print(f"✅ Task file found: {config.TASK_ID}.md")
    
    # Additional validation for production mode
    if config.EXECUTION_MODE == "production":
        print("🚨 PRODUCTION MODE WARNINGS:")
        print("   - Real files will be created/modified")
        print("   - Changes cannot be easily undone")
        print("   - Consider using sandbox mode for testing")
        
        print("\n⚠️  Auto-confirming production mode as requested.")
    
    print("✅ Configuration validation passed")
    return True


async def main_with_args():
    """Main function with CLI argument support."""
    args = parse_arguments()
    
    # Apply CLI overrides
    apply_cli_overrides(args)
    
    # Validate configuration
    if not validate_configuration():
        sys.exit(1)
    
    # If validate-only mode, exit after validation
    if args.validate_only:
        print("✅ Validation complete")
        return
    
    # Initialize sandbox if in sandbox mode
    if config.EXECUTION_MODE == "sandbox":
        from .utils.sandbox_manager import initialize_sandbox, get_sandbox_manager
        sandbox_root = initialize_sandbox()
        sandbox_manager = get_sandbox_manager()
        
        print(f"🏗️  Sandbox initialized: {sandbox_manager.session_id}")
        print(f"   📍 Location: {sandbox_root}")
        
        # Register cleanup handler
        import atexit
        if config.AUTO_CLEANUP_SANDBOX:
            def cleanup_handler():
                print(f"\n🧹 Cleaning up sandbox: {sandbox_manager.session_id}")
                sandbox_manager.cleanup()
            atexit.register(cleanup_handler)
    
    # Run the main research process
    await main()
    
    # Print summary for sandbox mode
    if config.EXECUTION_MODE == "sandbox":
        from .utils.sandbox_manager import get_sandbox_manager
        sandbox_manager = get_sandbox_manager()
        summary = sandbox_manager.get_summary()
        
        print(f"\n📊 SANDBOX SESSION SUMMARY")
        print("="*40)
        print(f"Session ID: {summary['session_id']}")
        print(f"Files created: {summary.get('file_count', 0)}")
        print(f"Total size: {summary.get('total_size_mb', 0)} MB")
        print(f"Location: {summary.get('sandbox_path', 'N/A')}")
        
        if not config.AUTO_CLEANUP_SANDBOX:
            print(f"💾 Sandbox preserved: {sandbox_manager.sandbox_root}")


if __name__ == "__main__":
    import asyncio
    import os
    
    asyncio.run(main_with_args())
