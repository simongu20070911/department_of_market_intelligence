"""
Base prompt components used across all agents.
These define common patterns and ensure consistency.
"""

# Base communication protocol used by ALL agents
COMMUNICATION_PROTOCOL = """### COMMUNICATION PROTOCOL - CRITICAL ###
ALWAYS start your response with:
🤔 [{agent_name}]: Examining the session state to understand what's needed...

Then EXPLICITLY mention:
- 📁 Working directory: {outputs_dir}
- 📖 Reading from: [specific file paths]
- 💾 Writing to: [specific file paths] 
- 🎯 Current task: {current_task}"""

# Base context template
BASE_CONTEXT = """### Context & State ###
You will operate based on the 'current_task' key in the session state: {current_task}
Today's date is: {current_date}
Current year: {current_year}"""

# Standard output format
OUTPUT_FORMAT = """### Output Format ###
You MUST end every response with "<end of output>"."""

# Time context reminder
TIME_CONTEXT = """### Important Time Context ###
Today's date is: {current_date}
Current year: {current_year}
Remember: You cannot analyze future data. Any analysis period must end on or before today's date."""

# File path context
FILE_PATH_CONTEXT = """### Working Environment ###
📁 PROJECT WORKSPACE: /home/gaen/agents_gaen/department_of_market_intelligence/
📊 CURRENT TASK ID: {task_id}
🎯 OUTPUTS DIRECTORY: {outputs_dir}
📋 TASK FILE: {task_file_path}"""