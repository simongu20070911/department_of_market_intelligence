# Workflow Error Detection - Complete Guide with Examples

## Quick Reference - When to Use Each Error Level

### 🚨 CRITICAL_WORKFLOW_ERROR - Pipeline WILL STOP
Use when continuing is **impossible** or would cause data corruption.

### ❌ WORKFLOW_ERROR - Major Problem
Use for significant issues that need attention but might be recoverable.

### ⚠️ WORKFLOW_WARNING - Minor Issue
Use for issues to note but can safely continue.

---

## CRITICAL ERROR Examples (Pipeline Stops Immediately)

### Example 1: Missing Essential File
```
Agent detects: The research plan file that should exist is missing
Agent outputs: 🚨 CRITICAL_WORKFLOW_ERROR: Research plan file not found at expected path /outputs/planning/research_plan_v1.md - cannot proceed with validation

Result: Pipeline stops immediately
```

### Example 2: Invalid Session State
```
Agent detects: Session state is missing required fields
Agent outputs: 🚨 CRITICAL_WORKFLOW_ERROR: Session state missing 'task_id' - workflow cannot determine which task to execute

Result: Pipeline stops immediately
```

### Example 3: Tool Failure
```
Agent detects: MCP Desktop Commander tool is not responding
Agent outputs: 🚨 CRITICAL_WORKFLOW_ERROR: Desktop Commander tool connection lost - cannot read or write files

Result: Pipeline stops immediately
```

### Example 4: Circular Dependency Detected
```
Agent detects: Task A depends on Task B, which depends on Task A
Agent outputs: 🚨 CRITICAL_WORKFLOW_ERROR: Circular dependency detected between tasks 'data_simulation' and 'statistical_analysis' - cannot determine execution order

Result: Pipeline stops immediately
```

### Example 5: Data Corruption
```
Agent detects: Output file has corrupted JSON that cannot be parsed
Agent outputs: 🚨 CRITICAL_WORKFLOW_ERROR: Implementation manifest JSON is corrupted and cannot be parsed - invalid syntax at line 45

Result: Pipeline stops immediately
```

---

## ERROR Examples (Significant Problems)

### Example 1: Recoverable File Issue
```
Agent detects: Expected file missing but can recreate
Agent outputs: ❌ WORKFLOW_ERROR: Statistical results file missing but can be regenerated from raw data

Result: Pipeline continues but issue is logged
```

### Example 2: Partial Data Loss
```
Agent detects: Some experiment results missing
Agent outputs: ❌ WORKFLOW_ERROR: 3 out of 10 simulation results are missing - continuing with available data

Result: Pipeline continues with degraded results
```

---

## WARNING Examples (Minor Issues)

### Example 1: Using Defaults
```
Agent detects: Configuration parameter missing
Agent outputs: ⚠️ WORKFLOW_WARNING: No random seed specified - using default value 42

Result: Pipeline continues normally
```

### Example 2: Performance Issue
```
Agent detects: Process taking longer than expected
Agent outputs: ⚠️ WORKFLOW_WARNING: Simulation taking 5x longer than estimated - may timeout

Result: Pipeline continues but user is warned
```

---

## Complete Code Examples for Agents

### For Validators
```python
# In your validation logic:
if not os.path.exists(artifact_path):
    print("🚨 CRITICAL_WORKFLOW_ERROR: Cannot validate non-existent artifact at " + artifact_path)
    # The pipeline will stop here
```

### For Experiment Executor
```python
# When checking experiment setup:
if not experiments:
    print("🚨 CRITICAL_WORKFLOW_ERROR: No executable experiments found in manifest - implementation plan may be corrupted")
    # The pipeline will stop here
```

### For Chief Researcher
```python
# When loading task description:
try:
    task_content = read_file(task_file_path)
except FileNotFoundError:
    print(f"🚨 CRITICAL_WORKFLOW_ERROR: Task description file not found at {task_file_path} - cannot proceed without knowing what to research")
    # The pipeline will stop here
```

### For Orchestrator
```python
# When parsing dependencies:
if has_circular_dependency(tasks):
    print(f"🚨 CRITICAL_WORKFLOW_ERROR: Circular dependency detected in task graph - cannot determine execution order")
    # The pipeline will stop here
```

---

## Decision Tree for Agents

```
Is the issue preventing me from completing my core task?
├─ YES → Can I work around it?
│   ├─ NO → 🚨 CRITICAL_WORKFLOW_ERROR
│   └─ YES → ❌ WORKFLOW_ERROR
└─ NO → Is it important to note?
    ├─ YES → ⚠️ WORKFLOW_WARNING
    └─ NO → Don't report
```

---

## Common Scenarios and Correct Responses

| Scenario | Correct Response |
|----------|-----------------|
| File I need to read doesn't exist | 🚨 CRITICAL_WORKFLOW_ERROR |
| Output directory doesn't exist (but I can create it) | Create it, no error |
| JSON parsing fails on critical config | 🚨 CRITICAL_WORKFLOW_ERROR |
| Missing optional parameter | ⚠️ WORKFLOW_WARNING |
| Tool timeout on critical operation | 🚨 CRITICAL_WORKFLOW_ERROR |
| Tool timeout on optional operation | ❌ WORKFLOW_ERROR |
| Validation found major issues in plan | Normal validation output (not workflow error) |
| Cannot write validation report | 🚨 CRITICAL_WORKFLOW_ERROR |
| Unexpected data format but can adapt | ⚠️ WORKFLOW_WARNING |
| Session state missing my task | 🚨 CRITICAL_WORKFLOW_ERROR |

---

## What Happens When You Signal an Error

### For CRITICAL_WORKFLOW_ERROR:
1. Your message is immediately displayed
2. The entire pipeline stops
3. Error is saved to checkpoint
4. User sees clear error summary
5. Pipeline exits with error status

### For WORKFLOW_ERROR:
1. Your message is logged
2. Pipeline continues
3. Error appears in final summary
4. User can review and decide action

### For WORKFLOW_WARNING:
1. Your message is logged
2. Pipeline continues normally
3. Warning appears in final summary
4. Helps with debugging if issues arise

---

## Template for Agents

When you detect an issue, output EXACTLY this format:

```
[One of these markers]: [Specific description of the problem]

Examples:
🚨 CRITICAL_WORKFLOW_ERROR: Research plan file not found at /outputs/planning/research_plan_v1.md - cannot proceed
❌ WORKFLOW_ERROR: Failed to generate visualization but analysis can continue
⚠️ WORKFLOW_WARNING: Using default batch size of 1000 as none specified
```

IMPORTANT: 
- Put the error marker at the START of a new line
- Include SPECIFIC details (paths, error messages, what failed)
- Explain WHY it's critical (what can't be done)
- Be concise but complete