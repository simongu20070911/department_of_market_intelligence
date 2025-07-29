"""
Experiment Executor agent prompt construction.
"""

from ..builder import PromptBuilder
from ..components.personas import EXPERIMENT_EXECUTOR_PERSONA
from ..components.tasks import EXECUTE_EXPERIMENTS_TASK


def build_executor_prompt() -> str:
    """Build the Experiment Executor prompt from components."""
    builder = PromptBuilder()
    
    # Add executor-specific context
    executor_context = """### Context & State ###
- The implementation plan is in the artifact at `state['implementation_manifest_artifact']`.
- The code to execute is in the artifacts listed in the manifest."""
    
    return builder\
        .add_persona(EXPERIMENT_EXECUTOR_PERSONA)\
        .add_communication_protocol()\
        .add_section(executor_context)\
        .add_section(EXECUTE_EXPERIMENTS_TASK)\
        .add_output_format()\
        .build()


# Export the built prompt
EXPERIMENT_EXECUTOR_INSTRUCTION = build_executor_prompt()