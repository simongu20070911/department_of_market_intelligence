"""
Chief Researcher agent prompt construction.
"""

from ..builder import PromptBuilder
from ..components.personas import CHIEF_RESEARCHER_PERSONA
from ..components.tasks import (
    GENERATE_INITIAL_PLAN_TASK,
    REFINE_PLAN_TASK,
    GENERATE_FINAL_REPORT_TASK
)

# Build the Chief Researcher instruction using components
CHIEF_RESEARCHER_INSTRUCTION = (
    PromptBuilder()
    .add_section("### Persona ###")
    .add_section(CHIEF_RESEARCHER_PERSONA)
    .add_communication_protocol_with_path_validation()
    .add_directory_structure_spec()
    .add_context()
    .add_time_context()
    .add_tasks([
        GENERATE_INITIAL_PLAN_TASK,
        REFINE_PLAN_TASK,
        GENERATE_FINAL_REPORT_TASK
    ])
    .add_output_format()
    .build()
)