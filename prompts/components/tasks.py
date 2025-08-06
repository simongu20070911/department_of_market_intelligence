"""
Task-specific instructions for agents.
"""

# Chief Researcher Tasks
GENERATE_INITIAL_PLAN_TASK = """### Task: 'generate_initial_plan' ###
If the current task is 'generate_initial_plan':

### RESEARCH TASK DESCRIPTION ###
{task_description}

### EXISTING WORK CONTEXT ###
{previous_critiques}

### PARALLEL VALIDATION FEEDBACK ###
{parallel_validation_feedback}

{existing_plans}

### ENVIRONMENTAL EXPLORATION ###
Use your tools to explore the environment and understand:
- Available data sources in {outputs_dir}/data/ (use `list_directory`)
- Current workspace structure and any existing scripts
- External data sources mentioned in the task that need to be acquired

1.  Based on the research task description and existing work context above, generate a comprehensive, step-by-step research plan. The plan MUST include:
    - A clear hypothesis.
    - Detailed data sourcing and hygiene protocols.
    - A list of specific experiments to be conducted, including statistical tests to be used (e.g., t-tests, regression analysis, stationarity tests).
    - A list of required outputs, charts, and metrics needed to validate the hypothesis.
    - Proactively identify and include experiments for any potentially interesting secondary relationships observed in the problem description.
2.  CRITICAL: First ensure the directory exists by using `create_directory` for `{outputs_dir}/planning/` if needed.
3.  Then use the `write_file` tool to save this plan to a new file. The full path MUST be `{outputs_dir}/planning/research_plan_v0.md`.
4.  IMPORTANT: Make each tool call separately - do not attempt to make multiple tool calls in one response.

### FILE CREATION RULES ###
- ✅ Use `write_file` to CREATE new files
- ❌ NEVER use `edit_file` - this is for refinement agents only
- ❌ NEVER modify existing files like critiques or previous plans
- If this is a retry after validation feedback, create a NEW version (v1, v2, etc.)"""

REFINE_PLAN_TASK = """### Task: 'refine_plan' ###
If the current task is 'refine_plan':

### CURRENT RESEARCH PLAN (Version {plan_version?}) ###
{research_plan}

### VALIDATION FEEDBACK ###
{previous_critiques}

### PARALLEL VALIDATION FEEDBACK (FROM SPECIALIZED VALIDATORS) ###
{parallel_validation_feedback}

### CRITICAL INSTRUCTIONS FOR ADDRESSING CRITIQUES ###
**DO NOT ARGUE WITH THE VALIDATORS' FEEDBACK. YOUR ROLE IS TO IMPROVE THE PLAN BY DIRECTLY ADDRESSING EACH CRITIQUE.**

- Accept all validator feedback as valid and constructive
- Do not justify or defend previous choices that were critiqued
- For each critique point, implement a concrete improvement in the revised plan
- If a validator says something is missing, add it
- If a validator says something needs clarification, clarify it
- If a validator suggests a specific approach, adopt it unless technically impossible
- **CRITICAL: Address ALL issues from parallel validation feedback - these are from specialized domain experts**

### ENVIRONMENTAL REASSESSMENT ###
Use your tools to check for any new data sources or workspace changes:
- Check {outputs_dir}/data/ for new datasets
- Review {outputs_dir}/workspace/ for any prototype implementations
- Understand current data availability and constraints

1.  The current plan version is: {plan_version?}
2.  Based on the current research plan, validation feedback, and environmental reassessment, meticulously revise the plan to address EVERY SINGLE POINT in the critique. Your revised plan must demonstrate that you have fully incorporated all feedback.
3.  **IMPORTANT**: Pay special attention to parallel validation feedback - these represent critical issues found by specialized validators
4.  The new plan must be a complete, standalone document that shows clear improvements based on the validators' guidance.

### CRITICAL FILE VERSIONING RULES ###
**NEVER EDIT EXISTING FILES - ALWAYS CREATE NEW VERSIONS**
- ❌ NEVER use `edit_file` on existing plans or critiques
- ❌ NEVER overwrite `research_plan_v0.md`, `research_plan_v1.md`, etc.
- ✅ ALWAYS create a NEW file with incremented version number
- ✅ The new version number should be {plan_version?} + 1
- ✅ Use `write_file` to save the NEW plan to `{outputs_dir}/planning/research_plan_v{next_version}.md`

### SURGICAL PRECISION REQUIREMENTS ###
- ONLY modify sections that address validator feedback
- Keep all other sections EXACTLY as they were in the previous version
- For each critique point:
  - Quote the specific critique
  - Show the exact change made to address it
  - Preserve everything else unchanged
- Do NOT make "improvements" beyond what was requested
- Do NOT reformat or reorganize unless specifically critiqued"""

GENERATE_FINAL_REPORT_TASK = """### Task: 'generate_final_report' ###
If the current task is 'generate_final_report':
1.  Load the final approved research plan from {plan_artifact_name?}.
2.  Load the final, aggregated experiment results from {results_artifact_name?}.
3.  Synthesize all information into a comprehensive, publication-quality research report. The report must directly address the goals and required outputs outlined in the plan.
4.  Use `write_file` to save the report to `{outputs_dir}/results/deliverables/final_report.md`."""

# Orchestrator Tasks
GENERATE_IMPLEMENTATION_PLAN_TASK = """### Task: 'generate_implementation_plan' ###
If `state['current_task']` is 'generate_implementation_plan':

### RESEARCH PLAN CONTEXT ###
{research_plan}

### TASK DESCRIPTION ###
{task_description}

### VALIDATION FEEDBACK ###
{validation_feedback}

### ENVIRONMENT EXPLORATION ###
Use your tools to understand the current environment:
- Check available data sources in {outputs_dir}/data/ (use `list_directory`)
- Examine workspace structure in {outputs_dir}/workspace/ for existing tools
- Identify any external data requirements that need acquisition
- Assess computational resource availability for parallel execution

1.  Based on the research plan context above and environmental assessment:
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
5.  Use `write_file` to save to `{outputs_dir}/planning/implementation_manifest.json`."""

GENERATE_RESULTS_EXTRACTION_PLAN_TASK = """### Task: 'generate_results_extraction_plan' ###
If `state['current_task']` is 'generate_results_extraction_plan':
1.  Load the Chief Researcher's plan from `state['plan_artifact_name']`.
2.  Load the implementation manifest from `state['implementation_manifest_artifact']`.
3.  Analyze the experiment logs and output artifacts (filenames will be in the manifest) to understand where the results are.
4.  Generate a single, clean Python script that:
    - Loads all necessary result artifacts.
    - Processes and aggregates them.
    - Produces the final charts, tables, and metrics required by the Chief Researcher's plan.
5.  Use `write_file` to save this script to `{outputs_dir}/workspace/scripts/results_extraction.py`."""

# Executor Tasks
EXECUTE_EXPERIMENTS_TASK = """### Task ###
1.  Read the implementation manifest from `state['implementation_manifest_artifact']`.
    - If manifest doesn't exist: 🚨 CRITICAL_WORKFLOW_ERROR: Implementation manifest not found at [path] - cannot execute experiments without knowing what to run
2.  Execute the scripts in the correct order based on their dependencies. Use the `start_process` tool to run each Python script.
3.  Keep a detailed journal of every command you run, its output, and any errors encountered.
4.  If a script fails with a critical, unrecoverable error that indicates a flaw in the code's logic (NOT a transient issue like a network timeout):
    a. Write your complete journal, including the detailed error, to an artifact named `outputs/execution_error_report.md`.
    b. Set the session state: `state['execution_status'] = 'critical_error'`.
    c. Set the session state: `state['error_report_artifact'] = 'outputs/execution_error_report.md'`.
    d. STOP further execution.
5.  If all scripts execute successfully:
    a. Write your complete journal to an artifact named `outputs/execution_journal.md`.
    b. Set the session state: `state['execution_status'] = 'success'`.

### WORKFLOW ERROR EXAMPLES FOR THIS TASK ###
- Manifest file missing: 🚨 CRITICAL_WORKFLOW_ERROR: Implementation manifest not found at /outputs/planning/implementation_manifest.json - cannot determine experiments to execute
- Manifest corrupted: 🚨 CRITICAL_WORKFLOW_ERROR: Implementation manifest JSON is invalid at line 15 - cannot parse experiment definitions
- Tool failure: 🚨 CRITICAL_WORKFLOW_ERROR: Desktop Commander start_process failed - cannot execute Python scripts
- Missing dependency: ❌ WORKFLOW_ERROR: Script dependency 'pandas' not installed - experiment may fail
- Long runtime: ⚠️ WORKFLOW_WARNING: Experiment taking 10x longer than estimated - may timeout"""

# Validator Tasks
JUNIOR_VALIDATOR_CORE_TASK = """### ARTIFACT TO VALIDATE ###
{artifact_content}

### RELATED RESEARCH PLAN ###
{research_plan}

1. Review the artifact content provided above (type: {validation_context?})
2. Apply context-specific validation based on the artifact type:

{context_specific_prompt}"""

SENIOR_VALIDATOR_CORE_TASK = """### ARTIFACT TO VALIDATE ###
{artifact_content}

### JUNIOR VALIDATOR FEEDBACK ###
{junior_critique}

### ORIGINAL RESEARCH PLAN ###
{research_plan}

### PREVIOUS SENIOR CRITIQUES ###
{previous_senior_critiques}

CRITICAL INSTRUCTION: All content above has been PRE-LOADED for your analysis. DO NOT use the read_file tool - analyze the content provided above.

1. Review the artifact content and junior validator feedback PROVIDED ABOVE
2. Apply deep, context-specific analysis based on the artifact type ({validation_context?}):

{context_specific_prompt}"""

# Validator Output Requirements
JUNIOR_VALIDATOR_OUTPUT_REQUIREMENTS = """### OUTPUT FORMAT FOR JUNIOR VALIDATOR ###
Structure your bug report EXACTLY as follows:

**1. SUMMARY**
   - Overall assessment and total finding count
   - Final verdict sentence

**2. CRITICAL ERRORS** (Issues that break the approach)
   - List each with location quote and detailed explanation

**3. MAJOR GAPS** (Significant omissions that must be addressed) 
   - List each with location quote and impact assessment

**4. MINOR ISSUES** (Improvements for rigor)
   - List each briefly

**5. DETAILED VERIFICATION LOG**
   - Step-by-step check of EVERY section
   - Quote relevant text before analysis
   - Justify correct steps briefly
   - Explain issues in detail

- Use `write_file` to save to `{outputs_dir}/planning/critiques/junior_critique_v{validation_version}.md`
- END with: **FINAL VALIDATION STATUS: [approved|rejected|critical_error]**"""

# Senior Validator Specific Tasks
SENIOR_VALIDATOR_COMPREHENSIVE_ANALYSIS = """IMPORTANT: All necessary content has been PRE-LOADED in the sections above. DO NOT attempt to read files.

You have access to comprehensive context pre-loaded above. Use this PRE-LOADED context to:
- Analyze the artifact content provided in the "ARTIFACT TO VALIDATE" section
- Review the junior validator's findings in the "JUNIOR VALIDATOR FEEDBACK" section
- Consider the original goals from the "ORIGINAL RESEARCH PLAN" section
- Learn from patterns in the "PREVIOUS SENIOR CRITIQUES" section
- Build a complete understanding of the work's evolution and quality

DO NOT use the read_file tool - everything you need is already loaded above."""

SENIOR_VALIDATOR_SYNTHESIS = """### SENIOR VALIDATOR OUTPUT FORMAT ###

1. **REVIEW OF JUNIOR'S FINDINGS**
   For each Junior finding, state:
   - ACCEPT ✓ or REJECT ✗ 
   - Your reasoning for accepting/rejecting
   
2. **FILTERED BUG REPORT**
   Only include findings you ACCEPTED from Junior:
   - Critical Errors (if any remain after filtering)
   - Major Gaps (if any remain after filtering)
   - Minor Issues (only if truly valuable)
   
3. **STRATEGIC ASSESSMENT**
   Your own high-level evaluation:
   - Does it meet business objectives?
   - Is the approach practical?
   - Are deliverables appropriate?
   
4. **FINAL CURATED FINDINGS**
   Clean list of issues that MUST be addressed

Write to `{outputs_dir}/planning/critiques/senior_critique_v{validation_version}.md`

Make final judgment:
   - END your critique file with: **FINAL VALIDATION STATUS: [approved|rejected|critical_error]**
   - 'approved': Work meets all quality standards
   - 'rejected': Needs refinement but fixable
   - 'critical_error': Fundamental issues requiring major rework"""

SENIOR_VALIDATOR_DECISION_CRITERIA = """- For 'approved': No critical issues, minor improvements optional
- For 'rejected': Issues that must be fixed but approach is sound
- For 'critical_error': Fundamental flaws in approach or execution"""

# Validator Restrictions
VALIDATOR_RESTRICTIONS = """- You are a VALIDATOR only - you MUST NOT edit, modify, or rewrite the research plan
- Your job is to CRITIQUE, not to fix or improve the original artifact
- ONLY create critique files, NEVER modify the research plan itself
- IMPORTANT: The artifact content and research plan are PRE-LOADED above - focus on analyzing them
- You may use tools if you need to check additional context, but the main content is already provided"""

SENIOR_VALIDATOR_RESTRICTIONS = """- You are a VALIDATOR only - you MUST NOT edit, modify, or rewrite the research plan
- Your job is to CRITIQUE and APPROVE/REJECT, not to fix or improve the original artifact
- ONLY create critique files, NEVER modify the research plan itself
- If you identify issues, document them in your critique - do NOT fix them yourself
- CRITICAL: ALL NECESSARY CONTENT IS PRE-LOADED ABOVE - DO NOT USE read_file TOOL
- The artifact content, junior critique, research plan, and previous critiques are ALREADY PROVIDED in the sections above
- FOCUS on analyzing the pre-loaded content and writing your critique file ONLY"""