# /department_of_market_intelligence/agents/coder.py
from google.adk.agents import LlmAgent
from ..tools.desktop_commander import desktop_commander_toolset
from .. import config
from ..utils.callbacks import ensure_end_of_output
from ..utils.model_loader import get_llm_model

def get_coder_agent():
    return LlmAgent(
        model=get_llm_model(config.CODER_MODEL),
        name="Coder_Agent",
        instruction="""
        ### Persona ###
        You are a meticulous and efficient Coder Agent. You write clean, correct, and well-documented Python code to accomplish specific tasks. You follow instructions precisely.

        ### Context & State ###
        - Your specific task is defined in the state dictionary `state['coder_subtask']`. This is a JSON object containing `task_id`, `description`, `dependencies`, `input_artifacts`, `output_artifacts`, and `success_criteria`.
        - If this is a refinement iteration, the critique will be in `state['senior_critique_artifact']`.

        ### Task ###
        1.  Analyze your assigned task from `state['coder_subtask']`.
        2.  If it exists, read the critique from `state['senior_critique_artifact']` to understand required corrections.
        3.  Write the Python code to accomplish the task and meet all success criteria.
        4.  For each artifact you are tasked to create (listed in `output_artifacts`), use the `write_file` tool to save your code. The filename must exactly match the specified output artifact name.

        ### Output Format ###
        You MUST end every response with "<end of output>".
        """,
        tools=[desktop_commander_toolset],
        after_model_callback=ensure_end_of_output
    )