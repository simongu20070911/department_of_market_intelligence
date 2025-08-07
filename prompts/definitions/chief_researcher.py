"""
Chief Researcher agent prompt construction.
"""

from ..builder import PromptBuilder
from ..components.personas import CHIEF_RESEARCHER_PERSONA
from ..components.researcher_tasks import (
    GENERATE_INITIAL_PLAN_TASK,
    REFINE_PLAN_TASK,
    FINAL_REPORT_TASK as GENERATE_FINAL_REPORT_TASK
)
from ..components.chief_researcher import CHIEF_RESEARCHER_STEP_INSTRUCTION

# Build the Chief Researcher instruction using components
CHIEF_RESEARCHER_INSTRUCTION = (
    PromptBuilder()
    .add_section("### Persona ###")
    .add_section(CHIEF_RESEARCHER_PERSONA)
    .add_communication_protocol()
    .add_directory_structure_spec()
    .add_context()
    .add_time_context()
    .add_tasks([
        GENERATE_INITIAL_PLAN_TASK,
        REFINE_PLAN_TASK,
        GENERATE_FINAL_REPORT_TASK
    ])
    .add_section("### Task Specifics ###")
    .add_section(CHIEF_RESEARCHER_STEP_INSTRUCTION)
    .add_output_format()
    .build()
)