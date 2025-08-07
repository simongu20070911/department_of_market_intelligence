"""
Prompt components for the Chief Researcher agent.
"""

CHIEF_RESEARCHER_STEP_INSTRUCTION = """
### TASK: {step_name}
### DESCRIPTION: {description}
### OUTPUT FILENAME: {filename}

Based on the overall research task below, generate the content for the specified output file.

### OVERALL RESEARCH TASK
{task_description}
"""