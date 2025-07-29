"""
Validation-specific focus areas for different contexts.
"""

RESEARCH_PLAN_VALIDATION = """### Validation Focus: Research Plan ###
Evaluate the research plan for:
- Hypothesis clarity and testability
- Data sourcing feasibility
- Statistical methodology rigor
- Timeline realism
- Output completeness"""

IMPLEMENTATION_MANIFEST_VALIDATION = """### Validation Focus: Implementation Manifest ###
Evaluate the implementation plan for:
- Task parallelization efficiency
- Interface contract completeness
- Resource allocation
- Dependency optimization
- Error handling robustness"""

RESULTS_EXTRACTION_VALIDATION = """### Validation Focus: Results Extraction ###
Evaluate the extraction script for:
- Coverage of all required outputs
- Data aggregation correctness
- Chart generation completeness
- Metric calculation accuracy
- Report formatting"""

FINAL_REPORT_VALIDATION = """### Validation Focus: Final Report ###
Evaluate the report for:
- Hypothesis validation completeness
- Results interpretation accuracy
- Statistical significance reporting
- Visualization quality
- Executive summary clarity"""

CODE_VALIDATION = """### Validation Focus: Code Quality ###
Evaluate the code for:
- Correctness and bug-free implementation
- Performance and efficiency
- Documentation completeness
- Error handling robustness
- Testing coverage"""

# Map contexts to their validation instructions
VALIDATION_CONTEXT_MAP = {
    "research_plan": RESEARCH_PLAN_VALIDATION,
    "implementation_manifest": IMPLEMENTATION_MANIFEST_VALIDATION,
    "results_extraction": RESULTS_EXTRACTION_VALIDATION,
    "final_report": FINAL_REPORT_VALIDATION,
    "code": CODE_VALIDATION
}