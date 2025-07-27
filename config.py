# /department_of_market_intelligence/config.py

import os
from dotenv import load_dotenv

load_dotenv() # Load variables from .env file

# --- Custom Gemini Endpoint Configuration ---
# If you have a custom base endpoint for the Gemini API, specify it here.
# If this is None or an empty string, the default endpoint will be used.
CUSTOM_GEMINI_API_ENDPOINT = os.getenv("CUSTOM_GEMINI_API_ENDPOINT", "http://0.0.0.0:8000")

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

# --- Tool Configurations ---
# This assumes the npx command is in the system's PATH
DESKTOP_COMMANDER_COMMAND = "npx"
DESKTOP_COMMANDER_ARGS = ["-y", "@wonderwhy-er/desktop-commander"]

# --- Output Validation ---
END_OF_OUTPUT_MARKER = "<end of output>"

# --- File Paths ---
TASKS_DIR = "tasks"
OUTPUTS_DIR = "outputs"