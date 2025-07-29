# /department_of_market_intelligence/prompts/components/contexts.py
"""Context and state definitions for agents."""

# Chief Researcher contexts
CHIEF_RESEARCHER_CONTEXT = """The research task description is:
{task_description}

You need to:
1. First understand the task
2. Develop a comprehensive research plan for quantitative market alpha 
3. Save the plan to the state"""

# Orchestrator contexts  
ORCHESTRATOR_CONTEXT = """- The research plan to implement is at `state['research_plan_artifact']`
- Current validation version: {validation_version}
- Task ID: {task_id}"""

# Experiment Executor contexts
EXPERIMENT_EXECUTOR_CONTEXT = """- The implementation plan is in the artifact at `state['implementation_manifest_artifact']`.
- The code to execute is in the artifacts listed in the manifest."""

# Coder contexts
CODER_CONTEXT = """- Your specific task is defined in the state dictionary `state['coder_subtask']`. This is a JSON object containing `task_id`, `description`, `dependencies`, `input_artifacts`, `output_artifacts`, and `success_criteria`.
- If this is a refinement iteration, the critique will be in `state['senior_critique_artifact']`."""

# Junior Validator contexts
JUNIOR_VALIDATOR_CONTEXT = """- Artifact to validate: {artifact_to_validate}
- Validation context: {validation_context?}
- Validation version: {validation_version}"""

# Senior Validator contexts
SENIOR_VALIDATOR_CONTEXT = """- Primary artifact: {artifact_to_validate}
- Junior critique: {junior_critique_artifact}
- Validation context: {validation_context?}
- Validation version: {validation_version}"""