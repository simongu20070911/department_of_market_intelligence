# Context-Aware Validation System

## Overview

The ULTRATHINK_QUANTITATIVEMarketAlpha department now features a sophisticated context-aware validation system that adapts validation criteria based on the type of artifact being validated. This ensures that validators focus on the most relevant issues for each phase of the research workflow.

## Key Features

### 1. **Automatic Context Detection**
- The system automatically detects what type of artifact is being validated based on:
  - Current workflow phase (planning, implementation, execution, results_extraction)
  - Current task name
  - Artifact filename patterns
- No confidence scores needed - we have full control over the workflow

### 2. **Context-Specific Validator Prompts**

#### Research Plan Validation
- **Junior Validator** focuses on:
  - Data availability edge cases
  - Statistical assumption failures
  - Market regime dependencies
  - Lookahead bias risks
  - Computational edge cases

- **Senior Validator** focuses on:
  - Statistical rigor & power analysis
  - Hypothesis clarity & testability
  - Data hygiene protocol completeness
  - Missing interesting relationships
  - Experimental design robustness
  - Result interpretation framework

#### Implementation Manifest Validation
- **Junior Validator** focuses on:
  - Missing task dependencies
  - Resource allocation conflicts
  - Undefined interface contracts
  - Error handling boundaries
  - Timing and timeout issues

- **Senior Validator** focuses on:
  - Parallelization efficiency
  - Surgical alignment clarity
  - Success criteria measurability
  - Task boundary definitions
  - Experiment logging structure
  - Research plan alignment

#### Code Implementation Validation
- **Junior Validator** focuses on:
  - Critical bugs (off-by-one, null handling)
  - Data leakage risks
  - Performance bottlenecks
  - Edge case handling
  - Integration failures

- **Senior Validator** focuses on:
  - Success criteria compliance
  - Interface contract adherence
  - Statistical implementation correctness
  - Data transformation validity
  - Integration readiness
  - Performance optimization

#### Experiment Execution Validation
- **Junior Validator** focuses on:
  - Missing experiment steps
  - Parameter setting errors
  - Data loading issues
  - Result storage problems
  - Environment issues

- **Senior Validator** focuses on:
  - Experimental protocol adherence
  - Statistical test execution correctness
  - Result completeness
  - Reproducibility documentation
  - Quality control checks
  - Execution journal quality

#### Results Extraction Validation
- **Junior Validator** focuses on:
  - Missing required outputs
  - Aggregation logic errors
  - Visualization problems
  - Calculation mistakes
  - Export format issues

- **Senior Validator** focuses on:
  - Research question coverage
  - Statistical summary accuracy
  - Result interpretation validity
  - Presentation clarity
  - Data integrity verification
  - Actionable insights extraction

### 3. **Parallel Final Validation**
- Uses specialized validators for comprehensive coverage:
  - Statistical Rigor Validator
  - Data Hygiene Validator
  - Methodology Validator
  - Efficiency Validator
  - General Validator

### 4. **Recursive Context Loading**
- Senior validators can recursively load additional context:
  - Explore directories with `list_directory`
  - Examine dependencies with `read_file`
  - Search for implementations with `search_code`
  - Build complete understanding of work in full context

## Configuration

Enable context-aware validation in `config.py`:

```python
# --- Validation Settings ---
ENABLE_CONTEXT_AWARE_VALIDATION = True  # Use context-aware validators
```

## Usage

When `ENABLE_CONTEXT_AWARE_VALIDATION` is enabled, the system automatically:

1. Uses `RootWorkflowAgentContextAware` instead of standard workflow
2. Detects validation context from workflow state
3. Applies appropriate validator prompts for each artifact type
4. Provides context-specific focus areas for validation

## Benefits

1. **More Relevant Validation**: Validators focus on issues specific to each artifact type
2. **Reduced False Positives**: Context-aware criteria prevent irrelevant critiques
3. **Better Coverage**: Each context has tailored validation points
4. **Improved Efficiency**: Validators know exactly what to look for
5. **Enhanced Quality**: Specialized validators catch domain-specific issues

## Architecture

```
ValidationContextManager
├── detect_validation_context()      # Fallback detection from filenames
├── prepare_validation_state()       # Sets context from workflow state
├── get_validator_focus_areas()      # Returns context-specific focus areas
└── inject_context_prompts()         # Injects prompts into validators

Context-Aware Validators
├── Junior Validator                 # Critical errors, edge cases
├── Senior Validator                 # Comprehensive analysis, judgment
├── Parallel Validators              # Specialized multi-perspective review
└── Meta Validator                   # Escalation decisions
```

## Testing

Run the context-aware validation tests:

```bash
python -m tests.test_context_aware_validation
python -m tests.test_enhanced_validator_prompts
```

## Future Enhancements

1. Add more specialized parallel validators for specific domains
2. Create validation templates for common research patterns
3. Add validation metrics and reporting
4. Implement validation history tracking
5. Create custom validation rules per project