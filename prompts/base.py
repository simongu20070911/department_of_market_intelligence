"""
Base prompt components used across all agents.
These define common patterns and ensure consistency.
"""

# Refined communication protocol
COMMUNICATION_PROTOCOL = """### COMMUNICATION PROTOCOL ###
1.  **Start with an emoji and your name**: `🤔 [{agent_name}]: Examining the session state...`
2.  **State your actions clearly**:
    -   `📁 Working directory: {outputs_dir}`
    -   `📖 Reading from: [List specific, validated file paths]`
    -   `💾 Writing to: [List specific, validated file paths]`
    -   `🎯 Current task: {current_task}`
3.  **Summarize your goal**: Briefly explain what you are about to do.
4.  **Use tools sequentially**: If multiple tool calls are needed, chain them in one response.
5.  **Wait for confirmation**: After using a tool, wait for the next turn to check the result before proceeding."""

# Refined error detection protocol
WORKFLOW_ERROR_DETECTION = """### WORKFLOW ERROR DETECTION ###
-   `🚨 CRITICAL_WORKFLOW_ERROR`: Use when you cannot continue (e.g., missing files, corrupted data).
-   `❌ WORKFLOW_ERROR`: Use for problems that degrade results but don't stop the workflow.
-   `⚠️ WORKFLOW_WARNING`: Use for minor issues where you can proceed with a workaround."""

# Path validation helper rules
PATH_VALIDATION_RULES = """### PATH VALIDATION RULES ###
Use these patterns for common file types:

📋 RESEARCH PLANS:
✅ `{outputs_dir}/planning/research_plan_v0.md`
✅ `{outputs_dir}/planning/research_plan_v1.md`
❌ `{outputs_dir}/research_plan_v0.md`

🔍 VALIDATION CRITIQUES:
✅ `{outputs_dir}/planning/critiques/junior_critique_v0.md`
✅ `{outputs_dir}/planning/critiques/senior_critique_v0.md`
❌ `{outputs_dir}/junior_critique_v0.md`
❌ `{outputs_dir}/planning/junior_critique_v0.md`

📊 IMPLEMENTATION MANIFESTS:
✅ `{outputs_dir}/planning/implementation_manifest.json`
❌ `{outputs_dir}/implementation_manifest.json`

🐍 ANALYSIS SCRIPTS:
✅ `{outputs_dir}/workspace/scripts/results_extraction.py`
✅ `{outputs_dir}/workspace/scripts/data_processing.py`
❌ `{outputs_dir}/results_extraction.py`

📈 FINAL REPORTS:
✅ `{outputs_dir}/results/deliverables/final_report.md`
❌ `{outputs_dir}/final_report.md`
❌ `outputs/final_report.md`

💾 DATA FILES:
✅ `{outputs_dir}/data/external/market_data.csv`
✅ `{outputs_dir}/data/processed/clean_data.csv`
✅ `{outputs_dir}/data/raw/raw_data.csv`
❌ `{outputs_dir}/market_data.csv`"""

# Base context template
BASE_CONTEXT = """### Context & State ###
You will operate based on the 'current_task' key in the session state: {current_task}
Today's date is: {current_date}
Current year: {current_year}"""

# Standard output format
OUTPUT_FORMAT = """### Output Format ###
You MUST end every response with "<end of output>"."""

# Validator-specific output format with status marker
VALIDATOR_OUTPUT_FORMAT = """### Validator Output Format ###
1. **File Content**: The content you write to your critique file MUST end with the status line:
   `**FINAL VALIDATION STATUS: [approved|rejected|critical_error]**`

2. **Final Response**: After you have finished all your work (including writing the file), your final response to me MUST end with the marker:
   `<end of output>`

**CRITICAL**: Do NOT put the `<end of output>` marker inside the content of the file you are writing. It must be at the very end of your final message to me.

Where status means:
- approved: No critical issues, work meets quality standards
- rejected: Issues found that require fixes, but approach is sound  
- critical_error: Fundamental flaws requiring major rework"""

# Time context reminder
TIME_CONTEXT = """### Important Time Context ###
Today's date is: {current_date}
Current year: {current_year}
Remember: You cannot analyze future data. Any analysis period must end on or before today's date."""

# Comprehensive directory structure specification
DIRECTORY_STRUCTURE_SPEC = """### CRITICAL: OUTPUT DIRECTORY STRUCTURE ###
Your outputs directory follows this EXACT structure. You MUST use these paths:

```
{outputs_dir}/
├── planning/
│   ├── research_plan_v0.md, v1.md, v2.md...     [Research plans - NEVER in root]
│   ├── implementation_manifest.json              [Task breakdown]
│   └── critiques/
│       ├── junior_critique_v0.md, v1.md...      [Junior validator feedback]
│       └── senior_critique_v0.md, v1.md...      [Senior validator feedback]
├── workspace/
│   ├── scripts/
│   │   └── results_extraction.py                [Analysis scripts]
│   ├── notebooks/                               [Jupyter notebooks]
│   ├── src/                                     [Source code]
│   └── tests/                                   [Test files]
├── results/
│   ├── deliverables/
│   │   ├── final_report.md                      [Final research report]
│   │   └── presentations/                       [Presentation materials]
│   ├── charts/                                  [Generated visualizations]
│   ├── execution_results.json                   [Experiment results]
│   └── statistical_results.json                 [Statistical outputs]
└── data/
    ├── external/                                [External data sources]
    ├── processed/                               [Processed datasets]
    └── raw/                                     [Raw data files]
```

### EXACT PATHS TO USE - DO NOT MODIFY:
✅ Research Plan: `{artifact_to_validate}` (READ THIS)
✅ Junior Critique: `{junior_critique_path}` (WRITE HERE - USE EXACT PATH)
✅ Senior Critique: `{senior_critique_path}` (WRITE HERE - USE EXACT PATH)
✅ Implementation Manifest: `{outputs_dir}/planning/implementation_manifest.json`
✅ Results Script: `{outputs_dir}/workspace/scripts/results_extraction.py`
✅ Final Report: `{outputs_dir}/results/deliverables/final_report.md`

### CRITICAL VIOLATIONS TO AVOID:
❌ NEVER: `{outputs_dir}/research_plan_v0.md` (missing planning/ subdirectory)
❌ NEVER: `{outputs_dir}/junior_critique_v0.md` (missing planning/critiques/ subdirectories)
❌ NEVER: `outputs/final_report.md` (missing task_id and results/deliverables/ subdirectories)
❌ NEVER: Any files directly in `{outputs_dir}/` root directory

### CRITICAL RULES:
1. NEVER create files directly in `{outputs_dir}/` root
2. ALWAYS use the appropriate nested subdirectory
3. Research plans go in `planning/`, NOT in root
4. Critiques go in `planning/critiques/`, NOT in root or `planning/`
5. Scripts go in `workspace/scripts/`, reports go in `results/deliverables/`
6. Before writing ANY file, CONFIRM the path follows the structure above"""