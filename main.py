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
            "Server connected successfully"
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
    litellm.set_verbose = True
    os.environ['LITELLM_LOG'] = 'DEBUG'
else:
    litellm.set_verbose = False
    os.environ['LITELLM_LOG'] = 'ERROR'

# Configure LiteLLM retries for server errors
os.environ['LITELLM_NUM_RETRIES'] = '3'
os.environ['LITELLM_RETRY_STRATEGY'] = 'exponential_backoff'
os.environ['LITELLM_RETRY_ON_STATUS_CODES'] = '429,500,502,503,504'

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
            
            # Restore session state from checkpoint
            initial_state = checkpoint_data['session_state']
            checkpoint_manager.agent_execution_count = checkpoint_data['agent_execution_count']
        else:
            print("❌ Failed to load checkpoint, starting fresh")
            initial_state = None
    else:
        print(f"🚀 STARTING NEW TASK: {config.TASK_ID}")
        initial_state = None

    # The root of our agentic system - using integrated context-aware validation
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
        
        initial_state = {"task_file_path": task_file_path}
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
        help='Resume from checkpoint'
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


def validate_configuration():
    """Validate system configuration before starting."""
    from .utils.tool_factory import validate_execution_mode, print_execution_mode_warning
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
        
        response = input("\n⚠️  Continue with production mode? (type 'YES'): ")
        if response != "YES":
            print("❌ Production mode cancelled")
            return False
    
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
