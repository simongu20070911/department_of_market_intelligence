# /department_of_market_intelligence/config.py
"""
Centralized configuration for the Department of Market Intelligence (DOMI) framework.
Environment variables are loaded from a .env file for easy customization.
"""

import os
from dotenv import load_dotenv
from typing import List, Dict
import json

load_dotenv()

# ==============================================================================
# --- API & MODEL CONFIGURATION ---
# ==============================================================================

# Custom Gemini API endpoint (e.g., for local models or proxies)
# If None or empty, the default Google API endpoint will be used.
CUSTOM_GEMINI_API_ENDPOINT = os.getenv("CUSTOM_GEMINI_API_ENDPOINT", "http://localhost:10000")

# API format toggle: "true" for OpenAI format, "false" for Gemini native format.
USE_OPENAI_FORMAT = os.getenv("USE_OPENAI_FORMAT", "true").lower() == "true"

# API key for custom endpoints that require specific authentication.
CUSTOM_API_KEY = os.getenv("CUSTOM_API_KEY", "not_needed")

# Model names for each agent role. Allows for using different models per agent.
AGENT_MODELS: Dict[str, str] = {
    "CHIEF_RESEARCHER": os.getenv("CHIEF_RESEARCHER_MODEL", "gemini-2.5-pro"),
    "ORCHESTRATOR": os.getenv("ORCHESTRATOR_MODEL", "gemini-2.5-pro"),
    "VALIDATOR": os.getenv("VALIDATOR_MODEL", "gemini-2.5-pro"),
    "CODER": os.getenv("CODER_MODEL", "gemini-2.5-pro"),
    "EXECUTOR": os.getenv("EXECUTOR_MODEL", "gemini-2.5-pro"),
}

# ==============================================================================
# --- WORKFLOW & EXECUTION CONFIGURATION ---
# ==============================================================================

# The primary task identifier, corresponding to a file in the /tasks directory.
TASK_ID = os.getenv("TASK_ID", "sample_research_task")

# Maximum number of parallel validators to use.
MAX_PARALLEL_VALIDATORS = int(os.getenv("MAX_PARALLEL_VALIDATORS", "4"))

# Maximum attempts for the implementation phase to recover from critical errors.
MAX_IMPLEMENTATION_ATTEMPTS = int(os.getenv("MAX_IMPLEMENTATION_ATTEMPTS", "3"))

# If True, allows workflow to proceed even if manifest validation fails after all retries.
# If False, a validation failure will halt the workflow.
ALLOW_MANIFEST_VALIDATION_FAIL_THROUGH = os.getenv("ALLOW_MANIFEST_VALIDATION_FAIL_THROUGH", "false").lower() == "true"

# If True, automatically pre-loads required files for each agent.
# If False, agents must read files manually using tools (slower but more explicit).
ENABLE_CONTEXT_PRELOADING = os.getenv("ENABLE_CONTEXT_PRELOADING", "true").lower() == "true"

# If True, streams agent thinking and actions to the console in real-time.
STREAMING_ENABLED = os.getenv("STREAMING_ENABLED", "true").lower() == "true"

# Marker to signify the end of an agent's output.
END_OF_OUTPUT_MARKER = "<end of output>"

# ==============================================================================
# --- CHECKPOINTING & RECOVERY ---
# ==============================================================================

# Master switch for the entire checkpointing system.
ENABLE_CHECKPOINTING = os.getenv("ENABLE_CHECKPOINTING", "true").lower() == "true"

# Master switch for the fine-grained micro-checkpointing system.
ENABLE_MICRO_CHECKPOINTS = os.getenv("ENABLE_MICRO_CHECKPOINTS", "true").lower() == "true"

# If True, automatically resumes from the latest micro-checkpoint if available.
MICRO_CHECKPOINT_AUTO_RESUME = os.getenv("MICRO_CHECKPOINT_AUTO_RESUME", "true").lower() == "true"

# Default maximum number of retries for a failed micro-checkpoint step.
MICRO_CHECKPOINT_MAX_RETRIES = int(os.getenv("MICRO_CHECKPOINT_MAX_RETRIES", "3"))

# Default timeout in seconds for a single micro-checkpoint step.
MICRO_CHECKPOINT_TIMEOUT = int(os.getenv("MICRO_CHECKPOINT_TIMEOUT", "300"))  # 5 minutes

# ==============================================================================
# --- DIRECTORY & PATH CONFIGURATION ---
# ==============================================================================

# Base directory of the project.
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Root directory for all task-related inputs.
TASKS_DIR = os.path.join(_BASE_DIR, "tasks")

# Root directory for all generated outputs.
OUTPUTS_BASE_DIR = os.path.join(_BASE_DIR, "outputs")

# Root directory for all checkpoint data.
CHECKPOINTS_BASE_DIR = os.path.join(_BASE_DIR, "checkpoints")

def get_task_specific_dir(base_dir: str, task_id: str = None) -> str:
    """Helper to get a task-specific directory path."""
    current_task_id = task_id or TASK_ID
    path = os.path.join(base_dir, current_task_id)
    os.makedirs(path, exist_ok=True)
    return path

def get_outputs_dir(task_id: str = None) -> str:
    """Get the output directory for a specific task."""
    return get_task_specific_dir(OUTPUTS_BASE_DIR, task_id)

def get_checkpoints_dir(task_id: str = None) -> str:
    """Get the checkpoints directory for a specific task."""
    return get_task_specific_dir(CHECKPOINTS_BASE_DIR, task_id)

# --- Sandbox Configuration ---
# Sandbox directory for safe execution. Defaults to a 'sandbox' folder within the project.
SANDBOX_BASE_DIR = os.getenv("SANDBOX_BASE_DIR", os.path.join(_BASE_DIR, "sandbox"))
# If False, the sandbox directory is preserved after each run.
AUTO_CLEANUP_SANDBOX = os.getenv("AUTO_CLEANUP_SANDBOX", "false").lower() == "true"

# ==============================================================================
# --- TOOL CONFIGURATION ---
# ==============================================================================

# Command to run the Desktop Commander MCP tool.
DESKTOP_COMMANDER_COMMAND = os.getenv("DESKTOP_COMMANDER_COMMAND", "npx")
DESKTOP_COMMANDER_ARGS: List[str] = ["-y", "@wonderwhy-er/desktop-commander"]

# Timeout in seconds for MCP tool operations.
MCP_TIMEOUT_SECONDS = int(os.getenv("MCP_TIMEOUT_SECONDS", "180"))

# ==============================================================================
# --- LOGGING & SAFETY ---
# ==============================================================================

# If True, enables verbose debug output from the framework and LiteLLM.
VERBOSE_LOGGING = os.getenv("VERBOSE_LOGGING", "false").lower() == "true"

# If True, the outputs directory will be cleared before each run.
CLEAR_OUTPUTS_ON_START = os.getenv("CLEAR_OUTPUTS_ON_START", "true").lower() == "true"