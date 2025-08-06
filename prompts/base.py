"""
Base prompt components used across all agents.
These define common patterns and ensure consistency.
"""

# Enhanced communication protocol with path validation
COMMUNICATION_PROTOCOL_WITH_PATH_VALIDATION = """### COMMUNICATION PROTOCOL WITH PATH VALIDATION - CRITICAL ###
ALWAYS start your response with:
🤔 [{agent_name}]: Examining the session state to understand what's needed...

Then EXPLICITLY mention (with PATH VALIDATION):
- 📁 Working directory: {outputs_dir}
- 📖 Reading from: [VALIDATE and list specific file paths that follow directory structure]
- 💾 Writing to: [VALIDATE and list specific file paths that follow directory structure]
- 🎯 Current task: {current_task}
- a summary of what you are going to do and aiming to do

Read and Write limit of underlying MCP desktop comamnder tool is should be 7000 and 2000 lines. If not, post a warning. 
Prioritize to write one file in once. 
Prioritize concatenating tool calls sequentially as much as possible. 
 - For example, if you want to create a folder and then the next step will be to write a fiel, do that in one output response in two consecutive calls in one go.
 - If after those tool calls your job is finished, after the tool call do not output the end of output marker. You must wait for the next turn, where you check if your job is done. 

### WORKFLOW ERROR DETECTION - CRITICAL FOR PIPELINE HEALTH ###

**WHEN TO STOP THE PIPELINE:**
Use 🚨 CRITICAL_WORKFLOW_ERROR when you CANNOT complete your task due to:
1. Missing files you need to read (e.g., research plan, manifest, task description)
2. Corrupted data that cannot be parsed (e.g., invalid JSON, malformed files)
3. Tool failures that prevent core operations (e.g., cannot read/write files)
4. Invalid or missing session state (e.g., no task_id, no artifact path)
5. Circular dependencies or logical impossibilities

**HOW TO SIGNAL ERRORS (EXACT FORMAT):**
Start a new line with the marker, then describe the specific problem:

🚨 CRITICAL_WORKFLOW_ERROR: [specific issue] - [why you cannot continue]
❌ WORKFLOW_ERROR: [problem description] - [impact on results]
⚠️ WORKFLOW_WARNING: [minor issue] - [what default/workaround is being used]

**REAL EXAMPLES FROM YOUR WORKFLOW:**

Example 1 - File doesn't exist:
🚨 CRITICAL_WORKFLOW_ERROR: Research plan not found at /outputs/planning/research_plan_v1.md - cannot validate non-existent artifact

Example 2 - Invalid data:
🚨 CRITICAL_WORKFLOW_ERROR: Implementation manifest JSON is corrupted at line 23 - cannot parse task dependencies

Example 3 - Tool failure:
🚨 CRITICAL_WORKFLOW_ERROR: Desktop Commander read_file failed after 3 retries - cannot access required data

Example 4 - Missing state:
🚨 CRITICAL_WORKFLOW_ERROR: Session state missing 'artifact_to_validate' - don't know what file to validate

Example 5 - Using defaults (warning only):
⚠️ WORKFLOW_WARNING: No temperature specified for LLM - using default 0.7

**DECISION RULE:**
Can you complete your core task despite this issue?
- NO → 🚨 CRITICAL_WORKFLOW_ERROR (pipeline stops)
- YES but degraded → ❌ WORKFLOW_ERROR (pipeline continues)
- YES with minor adjustment → ⚠️ WORKFLOW_WARNING (pipeline continues) 



### PATH VALIDATION REQUIREMENTS - CRITICAL ###
✅ BEFORE stating any file path, VERIFY it follows the directory structure:
- Research plans: `{outputs_dir}/planning/research_plan_v*.md` 
- Critiques: `{outputs_dir}/planning/critiques/[junior|senior]_critique_v*.md`
- Scripts: `{outputs_dir}/workspace/scripts/*.py`
- Reports: `{outputs_dir}/results/deliverables/*.md`
- Data: `{outputs_dir}/data/[external|processed|raw]/*`

❌ NEVER mention paths like:
- `{outputs_dir}/research_plan_v0.md` (missing planning/ subdirectory)
- `{outputs_dir}/critique_v0.md` (missing planning/critiques/ subdirectories)
- `outputs/final_report.md` (missing task_id and results/deliverables/ subdirectories)

🔍 PATH VALIDATION CHECKLIST:
1. Does the path include the correct nested subdirectory?
2. Does the path follow the {outputs_dir}/category/subcategory/ pattern?
3. Is the file type in the right location per directory structure?
4. Are you avoiding putting files directly in {outputs_dir}/ root?"""

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

# File path context
FILE_PATH_CONTEXT = """### Working Environment ###
📁 PROJECT WORKSPACE: /home/gaen/agents_gaen/department_of_market_intelligence/
📊 CURRENT TASK ID: {task_id}
🎯 OUTPUTS DIRECTORY: {outputs_dir}
📋 TASK FILE: {task_file_path}"""

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

### PATH EXAMPLES - USE THESE EXACT PATTERNS:
✅ Research Plan: `{outputs_dir}/planning/research_plan_v0.md`
✅ Junior Critique: `{outputs_dir}/planning/critiques/junior_critique_v{validation_version}.md`
✅ Senior Critique: `{outputs_dir}/planning/critiques/senior_critique_v{validation_version}.md`
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