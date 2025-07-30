# /department_of_market_intelligence/prompts/definitions/experiment_executor.py
from ..builder import PromptBuilder
from ..components.personas import EXPERIMENT_EXECUTOR_PERSONA
from ..components.contexts import EXPERIMENT_EXECUTOR_CONTEXT
from ..components.tasks import EXECUTE_EXPERIMENTS_TASK

EXPERIMENT_EXECUTOR_INSTRUCTION = (
    PromptBuilder()
    .add_section("### Persona ###")
    .add_section(EXPERIMENT_EXECUTOR_PERSONA)
    .add_communication_protocol()
    .add_section("### Context & State ###")
    .add_section(EXPERIMENT_EXECUTOR_CONTEXT)
    .add_section("### Task ###")
    .add_section(EXECUTE_EXPERIMENTS_TASK)
    .add_output_format()
    .build()
)