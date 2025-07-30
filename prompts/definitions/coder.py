# /department_of_market_intelligence/prompts/definitions/coder.py
from ..builder import PromptBuilder
from ..components.personas import CODER_PERSONA

CODER_INSTRUCTION = (
    PromptBuilder()
    .add_section("### Persona ###")
    .add_section(CODER_PERSONA)
    .add_communication_protocol()
    .add_directory_structure_spec()
    .add_section("### Context & State ###")
    .add_section("""- Your specific task is defined in the state dictionary `state['coder_subtask']`. This is a JSON object containing `task_id`, `description`, `dependencies`, `input_artifacts`, `output_artifacts`, and `success_criteria`.
- If this is a refinement iteration, the critique will be in `state['senior_critique_artifact']`.""")
    .add_section("### Task ###")
    .add_section("""1.  Analyze your assigned task from `state['coder_subtask']`.
2.  If it exists, read the critique from `state['senior_critique_artifact']` to understand required corrections.
3.  Write the Python code to accomplish the task and meet all success criteria.
4.  For each artifact you are tasked to create (listed in `output_artifacts`), use the `write_file` tool to save your code. The filename must exactly match the specified output artifact name.""")
    .add_output_format()
    .build()
)