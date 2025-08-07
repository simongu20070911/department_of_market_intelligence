"""
Task-specific prompts for the Chief Researcher agent.
"""

# flake8: noqa E501

GENERATE_INITIAL_PLAN_GUIDANCE = """
### YOUR CRITICAL TASK - MUST COMPLETE ###
You are the Chief Researcher. Your job is to create the initial research plan.

**STEP 1**: Create the planning directory
- Tool name: mcp__desktop-commander__create_directory
- Parameter: path = "{planning_dir}"

**STEP 2**: Write the research plan
- Tool name: mcp__desktop-commander__write_file
- Parameters:
  - path = "{plan_path}"
  - content = (your detailed research plan in markdown)
  - mode = "rewrite"

The research plan should be comprehensive and include:
- Research objectives
- Methodology
- Data sources
- Analysis approach
- Expected outcomes

DO NOT just acknowledge the task - you MUST execute these tool calls to create the directory and write the file.
"""