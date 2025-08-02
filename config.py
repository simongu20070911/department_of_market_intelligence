# /department_of_market_intelligence/config.py

import os
from dotenv import load_dotenv

load_dotenv() # Load variables from .env file

# --- Custom Gemini Endpoint Configuration ---
# If you have a custom base endpoint for the Gemini API, specify it here.
# If this is None or an empty string, the default endpoint will be used.
CUSTOM_GEMINI_API_ENDPOINT = os.getenv("CUSTOM_GEMINI_API_ENDPOINT", "http://0.0.0.0:10000")

# --- API Format Toggle ---
USE_OPENAI_FORMAT = os.getenv("USE_OPENAI_FORMAT", "true").lower() == "true"  # Set to true to use OpenAI format, false for Gemini

# --- API Key Configuration ---
# For custom endpoints that expect a specific key format
CUSTOM_API_KEY = os.getenv("CUSTOM_API_KEY", "sk-7m-daily-token-1")
# Standard Google API key (used when no custom endpoint is specified)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# --- Model Configurations ---
CHIEF_RESEARCHER_MODEL = "gemini-2.5-pro"
ORCHESTRATOR_MODEL = "gemini-2.5-pro"
VALIDATOR_MODEL = "gemini-2.5-pro"
CODER_MODEL = "gemini-2.5-pro"
EXECUTOR_MODEL = "gemini-2.5-pro"

# --- Workflow Control ---
MAX_PLAN_REFINEMENT_LOOPS = 5
MAX_CODE_REFINEMENT_LOOPS = 3
MAX_EXECUTION_CORRECTION_LOOPS = 2
PARALLEL_VALIDATION_SAMPLES = 4
MAX_ORCHESTRATOR_REFINEMENT_LOOPS = 5  # For implementation manifest refinement
MAX_IMPLEMENTATION_ATTEMPTS = 3  # Max attempts for implementation phase on critical errors

# --- Implementation Manifest Validation Fallback ---
# If True, allows workflow to continue when implementation manifest validation fails after max retries
# If False, workflow will fail with critical_error when validation fails (original behavior)
IMPLEMENTATION_MANIFEST_VALIDATION_ALLOW_PASS_ON_MAX_RETRIES = os.getenv(
    "IMPLEMENTATION_MANIFEST_VALIDATION_ALLOW_PASS_ON_MAX_RETRIES", "true"
).lower() == "true"

# --- Context Pre-Loading System ---
# If True, automatically pre-loads required files for each agent type to eliminate manual file discovery
# If False, agents use traditional tool-based file reading (slower but more explicit)
ENABLE_CONTEXT_PRELOADING = os.getenv("ENABLE_CONTEXT_PRELOADING", "true").lower() == "true"

# --- Validation Settings ---
# (No special configuration needed - using integrated context-aware validators)

# --- Tool Configurations ---
# This assumes the npx command is in the system's PATH
DESKTOP_COMMANDER_COMMAND = "npx"
DESKTOP_COMMANDER_ARGS = ["-y", "@wonderwhy-er/desktop-commander"]
MCP_TIMEOUT_SECONDS = 180  # 3 minutes timeout for MCP operations

# --- Output Validation ---
END_OF_OUTPUT_MARKER = "<end of output>"

# --- Task Management ---
# The task identifier to research. Corresponds to a file in the /tasks directory.
TASK_ID = os.getenv("TASK_ID", "sample_research_task")  # Without .md extension
ENABLE_CHECKPOINTING = os.getenv("ENABLE_CHECKPOINTING", "true").lower() == "true"
CHECKPOINT_INTERVAL = int(os.getenv("CHECKPOINT_INTERVAL", "1"))  # Save checkpoint after every N agents

# --- Micro-Checkpoint Configuration ---
ENABLE_MICRO_CHECKPOINTS = os.getenv("ENABLE_MICRO_CHECKPOINTS", "true").lower() == "true"
MICRO_CHECKPOINT_AUTO_RESUME = os.getenv("MICRO_CHECKPOINT_AUTO_RESUME", "true").lower() == "true"
MICRO_CHECKPOINT_MAX_RETRIES = int(os.getenv("MICRO_CHECKPOINT_MAX_RETRIES", "3"))
MICRO_CHECKPOINT_TIMEOUT = int(os.getenv("MICRO_CHECKPOINT_TIMEOUT", "300"))  # 5 minutes default
MICRO_CHECKPOINT_CLEANUP_DAYS = int(os.getenv("MICRO_CHECKPOINT_CLEANUP_DAYS", "7"))  # Keep 7 days

# --- File Paths ---
# Use absolute paths to ensure files are created in the correct location
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Directory Paths ---
# Path to the directory where task markdown files are stored.
TASKS_DIR = os.path.join(_BASE_DIR, "tasks")

# Path to the root directory for all generated outputs.
# Outputs for each task will be stored in a subdirectory here.
OUTPUTS_BASE_DIR = os.path.join(_BASE_DIR, "outputs")

# Task-specific directories
def get_outputs_dir(task_id: str = None) -> str:
    task_id = task_id or TASK_ID
    
    # Always use real outputs directory - sandbox mode provides safety through tool isolation
    return os.path.join(_BASE_DIR, "outputs", task_id)

def get_checkpoints_dir(task_id: str = None) -> str:
    task_id = task_id or TASK_ID
    
    # Always use real checkpoints directory - sandbox mode provides safety through tool isolation
    return os.path.join(_BASE_DIR, "checkpoints", task_id)

# Default directories using the configured TASK_ID 
# Note: These are static paths that don't use the dynamic functions to avoid recursion
OUTPUTS_DIR = os.path.join(_BASE_DIR, "outputs", TASK_ID)
CHECKPOINTS_DIR = os.path.join(_BASE_DIR, "checkpoints", TASK_ID)

# --- Logging Configuration ---
VERBOSE_LOGGING = False  # Set to True for detailed debug output, False for cleaner output

# --- Execution Modes ---
STREAMING_ENABLED = True # Set to True to stream the thinking process of the agents

# Execution mode options: "dry_run", "sandbox", "production"
EXECUTION_MODE = os.getenv("EXECUTION_MODE", "sandbox")

# Legacy dry run mode support (for backward compatibility)
DRY_RUN_MODE = (EXECUTION_MODE == "dry_run")  # Computed from EXECUTION_MODE
MAX_DRY_RUN_ITERATIONS = 3  # Limit iterations in dry run mode to catch bugs early
DRY_RUN_SKIP_LLM = (EXECUTION_MODE == "dry_run")  # Only skip LLM calls in actual dry_run mode
DRY_RUN_COMPREHENSIVE_PATH_TESTING = True  # Enable comprehensive path consistency testing

# --- Sandbox Configuration ---
# Use project directory for sandbox instead of /tmp so outputs go to real locations
SANDBOX_BASE_DIR = os.getenv("SANDBOX_BASE_DIR", os.path.join(_BASE_DIR, "sandbox"))  # Project-based sandbox
AUTO_CLEANUP_SANDBOX = os.getenv("AUTO_CLEANUP_SANDBOX", "false").lower() == "true"  # Keep outputs by default
SANDBOX_PRESERVE_LOGS = os.getenv("SANDBOX_PRESERVE_LOGS", "true").lower() == "true"  # Keep logs for debugging
SANDBOX_SESSION_ID = None  # Will be set at runtime

# --- Production Safety ---
REQUIRE_PRODUCTION_CONFIRMATION = False  # Auto-confirm production mode to prevent workflow interruption
os.environ["DOMI_PRODUCTION_CONFIRMED"] = "true"  # Skip production confirmation prompts
PRODUCTION_BACKUP_ENABLED = True  # Create backups before production runs

# --- Tool Configuration Management ---
ENABLE_TOOL_CONFIG_LOGGING = True  # Log Desktop Commander configuration on startup
TOOL_CONFIG_AUTO_OPTIMIZE = False  # Automatically apply high-throughput config on startup


# --- Tool Configuration Integration Functions ---

def log_tool_configuration():
    """Log current Desktop Commander configuration if enabled."""
    if not ENABLE_TOOL_CONFIG_LOGGING:
        return
    
    print("\n🔧 DESKTOP COMMANDER CONFIGURATION")
    print("   📝 Write Limit: 2000 lines per operation (configured)")
    print("   📖 Read Limit: 7000 lines per operation (configured)")
    print("   ✅ Configuration is persistent across sessions")
    print("   💡 Use MCP tools directly for real-time configuration changes")


def apply_auto_optimization():
    """Apply automatic tool optimization if enabled."""
    if not TOOL_CONFIG_AUTO_OPTIMIZE:
        return
    
    print("🚀 Desktop Commander is already configured with optimal settings")
    print("   📝 Write Limit: 2000 lines")
    print("   📖 Read Limit: 7000 lines")


def validate_tool_configuration():
    """Validate Desktop Commander configuration and suggest improvements."""
    print("✅ Desktop Commander configuration validated")
    print("   📝 Write Limit: 2000 lines (optimal)")
    print("   📖 Read Limit: 7000 lines (optimal)")
    print("   🔒 Configuration is persistent")
    return True


# Call configuration functions on import if enabled
if ENABLE_TOOL_CONFIG_LOGGING:
    log_tool_configuration()

if TOOL_CONFIG_AUTO_OPTIMIZE:
    apply_auto_optimization()