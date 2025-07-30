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
    return os.path.join(_BASE_DIR, "outputs", task_id)

def get_checkpoints_dir(task_id: str = None) -> str:
    task_id = task_id or TASK_ID
    return os.path.join(_BASE_DIR, "checkpoints", task_id)

# Default directories using the configured TASK_ID
OUTPUTS_DIR = get_outputs_dir()
CHECKPOINTS_DIR = get_checkpoints_dir()

# --- Logging Configuration ---
VERBOSE_LOGGING = False  # Set to True for detailed debug output, False for cleaner output

# --- Execution Modes ---
STREAMING_ENABLED = True # Set to True to stream the thinking process of the agents
DRY_RUN_MODE = False  # Set to True to validate workflows without executing expensive operations  
MAX_DRY_RUN_ITERATIONS = 3  # Limit iterations in dry run mode to catch bugs early
DRY_RUN_SKIP_LLM = True  # Skip LLM calls entirely in dry run mode
DRY_RUN_COMPREHENSIVE_PATH_TESTING = True  # Enable comprehensive path consistency testing