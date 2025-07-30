"""
Task-specific instructions for agents.
"""

# Chief Researcher Tasks
GENERATE_INITIAL_PLAN_TASK = """### Task: 'generate_initial_plan' ###
If the current task is 'generate_initial_plan':
1.  Read the research task description from the file path: {task_file_path} using the `read_file` tool.
2.  Generate a comprehensive, step-by-step research plan. The plan MUST include:
    - A clear hypothesis.
    - Detailed data sourcing and hygiene protocols.
    - A list of specific experiments to be conducted, including statistical tests to be used (e.g., t-tests, regression analysis, stationarity tests).
    - A list of required outputs, charts, and metrics needed to validate the hypothesis.
    - Proactively identify and include experiments for any potentially interesting secondary relationships observed in the problem description.
3.  Use the `write_file` tool to save this plan to a new file. The full path MUST be `{outputs_dir}/planning/research_plan_v0.md`.
4.  Update the session state: `state['plan_artifact_name'] = 'outputs/{task_id}/planning/research_plan_v0.md'`, `state['plan_version'] = 0`, and `state['artifact_to_validate'] = '{outputs_dir}/planning/research_plan_v0.md'`."""

REFINE_PLAN_TASK = """### Task: 'refine_plan' ###
If the current task is 'refine_plan':
1.  The current plan version is: {plan_version?}
2.  Load the current plan from {plan_artifact_name?} using `read_file`.
3.  Load the senior validator's critique from {critique_artifact_name?} using `read_file`.
4.  Meticulously revise the plan to address every point in the critique, enhancing its rigor and clarity. The new plan must be a complete, standalone document.
5.  Calculate the new version number as current plan_version + 1. Use `write_file` to save the new plan with the incremented version number.
6.  Update the session state with the new plan artifact name, increment the plan_version by 1, and update artifact_to_validate to point to the new version."""

GENERATE_FINAL_REPORT_TASK = """### Task: 'generate_final_report' ###
If the current task is 'generate_final_report':
1.  Load the final approved research plan from {plan_artifact_name?}.
2.  Load the final, aggregated experiment results from {results_artifact_name?}.
3.  Synthesize all information into a comprehensive, publication-quality research report. The report must directly address the goals and required outputs outlined in the plan.
4.  Use `write_file` to save the report to `{outputs_dir}/results/deliverables/final_report.md`."""

# Orchestrator Tasks
GENERATE_IMPLEMENTATION_PLAN_TASK = """### Task: 'generate_implementation_plan' ###
If `state['current_task']` is 'generate_implementation_plan':
1.  Load the final, approved research plan from `state['plan_artifact_name']` using `read_file`.
2.  CRITICAL: Analyze the plan to identify INDEPENDENT WORK STREAMS that can execute in parallel:
    - Separate data pipelines (market data, alternative data, fundamental data, risk data)
    - Independent feature engineering streams (technical, fundamental, sentiment, micro-structure)
    - Parallel model training (different model types, parameter sweeps)
    - Concurrent analysis streams (performance, risk, attribution)
    
3.  For EACH task, define a JSON object with these ENHANCED keys:
    - `task_id`: Unique identifier (e.g., 'market_data_fetch', 'alt_data_fetch', 'technical_features')
    - `description`: Detailed task description including computational requirements
    - `dependencies`: List of task_ids that MUST complete first (MINIMIZE THESE!)
    - `parallel_group`: Group ID for tasks that SHOULD run simultaneously
    - `estimated_runtime`: Expected execution time to optimize scheduling
    - `input_artifacts`: List of input artifact paths
    - `output_artifacts`: List of output artifact paths  
    - `interface_contract`: CRITICAL - Define exact data schema
    - `stitching_point`: If this task converges parallel streams, define how
    - `resource_requirements`: CPU cores, memory, GPU needs for optimal scheduling
    - `success_criteria`: Specific, measurable completion conditions
    - `can_fail_independently`: Boolean - if True, failure doesn't block parallel tasks
    
4.  Assemble task objects into JSON array, ensuring `parallel_group` assignments maximize concurrency.
5.  Use `write_file` to save to `{outputs_dir}/planning/implementation_manifest.json`.
6.  Update session state: `state['implementation_manifest_artifact'] = 'outputs/{task_id}/planning/implementation_manifest.json'`."""

GENERATE_RESULTS_EXTRACTION_PLAN_TASK = """### Task: 'generate_results_extraction_plan' ###
If `state['current_task']` is 'generate_results_extraction_plan':
1.  Load the Chief Researcher's plan from `state['plan_artifact_name']`.
2.  Load the implementation manifest from `state['implementation_manifest_artifact']`.
3.  Analyze the experiment logs and output artifacts (filenames will be in the manifest) to understand where the results are.
4.  Generate a single, clean Python script that:
    - Loads all necessary result artifacts.
    - Processes and aggregates them.
    - Produces the final charts, tables, and metrics required by the Chief Researcher's plan.
5.  Use `write_file` to save this script to `{outputs_dir}/workspace/scripts/results_extraction.py`.
6.  Update the session state: `state['results_extraction_script_artifact'] = 'outputs/{task_id}/workspace/scripts/results_extraction.py'`."""

# Executor Tasks
EXECUTE_EXPERIMENTS_TASK = """### Task ###
1.  Read the implementation manifest from `state['implementation_manifest_artifact']`.
2.  Execute the scripts in the correct order based on their dependencies. Use the `start_process` tool to run each Python script.
3.  Keep a detailed journal of every command you run, its output, and any errors encountered.
4.  If a script fails with a critical, unrecoverable error that indicates a flaw in the code's logic (NOT a transient issue like a network timeout):
    a. Write your complete journal, including the detailed error, to an artifact named `outputs/execution_error_report.md`.
    b. Set the session state: `state['execution_status'] = 'critical_error'`.
    c. Set the session state: `state['error_report_artifact'] = 'outputs/execution_error_report.md'`.
    d. STOP further execution.
5.  If all scripts execute successfully:
    a. Write your complete journal to an artifact named `outputs/execution_journal.md`.
    b. Set the session state: `state['execution_status'] = 'success'`."""

# Validator Tasks
JUNIOR_VALIDATOR_CORE_TASK = """1. Use the `read_file` tool to load the artifact specified in {artifact_to_validate}
2. Identify the validation context from {validation_context?} to understand what type of artifact you're validating
3. Apply context-specific validation based on the artifact type:

{context_specific_prompt}"""

SENIOR_VALIDATOR_CORE_TASK = """1. Load and analyze both the primary artifact and junior critique using `read_file`
2. Identify the validation context to understand what you're validating
3. Apply deep, context-specific analysis based on the artifact type:

{context_specific_prompt}"""

# Validator Output Requirements
JUNIOR_VALIDATOR_OUTPUT_REQUIREMENTS = """- If you find critical issues, list them clearly and concisely
- For each issue, explain WHY it's critical and its potential impact
- If no critical issues found, write: "No critical issues found."
- Use `write_file` to save your critique to `{outputs_dir}/planning/critiques/junior_critique_v{validation_version}.md`
- Include a section "Key Files Reviewed:" listing important files you examined"""

# Senior Validator Specific Tasks
SENIOR_VALIDATOR_RECURSIVE_LOADING = """You have the ability to recursively load additional context:
- Use `list_directory` to explore relevant directories
- Use `read_file` to examine dependencies, related files, or previous versions
- Use `search_code` to find implementations or definitions
- Build a complete understanding of the work in its full context"""

SENIOR_VALIDATOR_SYNTHESIS = """1. Synthesize junior validator findings with your comprehensive analysis
2. Write detailed critique to `{outputs_dir}/planning/critiques/senior_critique_v{validation_version}.md`
3. Include sections:
   - "Junior Validator Findings Addressed"
   - "Additional Critical Analysis"
   - "Recommendations for Improvement"
   - "Key Files Reviewed" (list all files examined)
   
4. Make final judgment - set `state['validation_status']` to:
   - 'approved': Work meets all quality standards
   - 'rejected': Needs refinement but fixable
   - 'critical_error': Fundamental issues requiring major rework"""

SENIOR_VALIDATOR_DECISION_CRITERIA = """- For 'approved': No critical issues, minor improvements optional
- For 'rejected': Issues that must be fixed but approach is sound
- For 'critical_error': Fundamental flaws in approach or execution"""

# Validator Restrictions
VALIDATOR_RESTRICTIONS = """- You are a VALIDATOR only - you MUST NOT edit, modify, or rewrite the research plan
- Your job is to CRITIQUE, not to fix or improve the original artifact
- ONLY create critique files, NEVER modify the research plan itself"""

SENIOR_VALIDATOR_RESTRICTIONS = """- You are a VALIDATOR only - you MUST NOT edit, modify, or rewrite the research plan
- Your job is to CRITIQUE and APPROVE/REJECT, not to fix or improve the original artifact
- ONLY create critique files, NEVER modify the research plan itself
- If you identify issues, document them in your critique - do NOT fix them yourself"""