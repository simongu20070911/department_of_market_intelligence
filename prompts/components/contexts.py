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
ORCHESTRATOR_CONTEXT = """- The research plan to implement is at `state['domi_research_plan_artifact']`
- Current validation version: {domi_validation_version}
- Task ID: {domi_task_id}"""

# Experiment Executor contexts
EXPERIMENT_EXECUTOR_CONTEXT = """- The implementation plan is in the artifact at `state['domi_implementation_manifest_artifact']`.
- The code to execute is in the artifacts listed in the manifest."""

# Coder contexts
CODER_CONTEXT = """- Your specific task is defined in the state dictionary `state['coder_subtask']`. This is a JSON object containing `task_id`, `description`, `dependencies`, `input_artifacts`, `output_artifacts`, and `success_criteria`.
- If this is a refinement iteration, the critique will be in `state['domi_senior_critique_artifact']`."""

# Junior Validator contexts
JUNIOR_VALIDATOR_CONTEXT = """- Task Description: {domi_task_description}
- Artifact to validate: {domi_artifact_to_validate}
- Validation context: {domi_validation_context?}
- Validation version: {domi_validation_version}"""

# Senior Validator contexts
SENIOR_VALIDATOR_CONTEXT = """- Task Description: {domi_task_description}
- Primary artifact: {domi_artifact_to_validate}
- Junior critique: {domi_junior_critique_artifact}
- Validation context: {domi_validation_context?}
- Validation version: {domi_validation_version}"""

# Validation context types
VALIDATION_CONTEXTS = {
    "research_plan": "Research Plan from Chief Researcher",
    "implementation_manifest": "Implementation Manifest from Orchestrator", 
    "code_implementation": "Code Implementation from Parallel Coders",
    "experiment_execution": "Experiment Execution Journal",
    "results_extraction": "Results Extraction Plan/Code"
}

# Junior validator context-specific prompts
JUNIOR_VALIDATION_PROMPTS = {
    "research_plan": """
            ### METICULOUS VERIFICATION INSTRUCTIONS ###
            You must perform a COMPREHENSIVE, STEP-BY-STEP verification of the entire research plan.
            Check EVERYTHING - assume nothing is correct until you verify it.
            
            **1. STATISTICAL METHODS - VERIFY EVERY TEST**:
               □ Is each statistical test appropriate for its data type?
               □ Are sample size requirements met for each test?
               □ Are distribution assumptions explicitly stated and testable?
               □ Are confidence intervals properly specified?
               □ Is multiple comparison correction applied where needed?
               □ Are effect size calculations included?
               □ Are power analyses conducted?
               □ Are null/alternative hypotheses clearly stated?
               
            **2. DATA REQUIREMENTS - CHECK EVERY SOURCE**:
               □ Does each data source actually exist and is it accessible?
               □ Is the data frequency appropriate for the analysis?
               □ Are data quality checks specified?
               □ Is missing data handling defined?
               □ Are outlier detection methods specified?
               □ Is data versioning addressed?
               □ Are there potential survivorship or look-ahead biases?
               
            **3. METHODOLOGY RIGOR - EXAMINE EVERY STEP**:
               □ Is the experimental design sound?
               □ Are control variables identified?
               □ Are confounding factors addressed?
               □ Is the sampling strategy appropriate?
               □ Are randomization procedures specified?
               □ Is reproducibility ensured (seeds, environment)?
               □ Are there untested assumptions?
               
            **4. IMPLEMENTATION FEASIBILITY - TEST EVERY CLAIM**:
               □ Can each proposed experiment actually be executed?
               □ Are computational resources sufficient?
               □ Do algorithms scale to the data size?
               □ Are all dependencies identified?
               □ Are implementation details complete?
               □ Are there missing technical specifications?
               
            **5. DELIVERABLES COMPLETENESS - VERIFY EVERY OUTPUT**:
               □ Does each required output have a generation method?
               □ Are all visualizations properly specified?
               □ Is the reporting structure complete?
               □ Are success metrics defined?
               □ Are validation procedures specified?
               
            **6. EDGE CASES AND FAILURE MODES**:
               □ What happens with empty datasets?
               □ How are numerical edge cases handled (division by zero, overflow)?
               □ What are the failure recovery procedures?
               □ Are there timeout specifications?
               □ How are partial failures handled?
               
            For EACH issue found, classify it as:
            - **CRITICAL ERROR**: Breaks the logical chain, invalidates approach
            - **MAJOR GAP**: Significant omission that must be addressed
            - **MINOR ISSUE**: Would improve rigor but not essential
            """,
    
    "implementation_manifest": """
            ### Critical Issues in Implementation Manifest ###
            Focus on these potential show-stoppers:
            
            0. **JSON VALIDITY - MUST CHECK FIRST**:
               - **CRITICAL**: Is the file valid, parseable JSON?
               - Try to parse it with a JSON parser - does it succeed?
               - Look for JavaScript code that doesn't belong in JSON:
                 * Spread operators (...Array)
                 * Array.from() or other JS methods
                 * Template literals with backticks
                 * Arrow functions (=>)
                 * Comments (// or /* */)
               - Check for proper JSON syntax:
                 * All strings in double quotes
                 * No trailing commas
                 * Boolean values lowercase (true/false)
                 * No undefined or null where not allowed
               - If JSON is invalid, mark as CRITICAL ERROR immediately
            
            1. **Missing Dependencies**:
               - Data dependencies not explicitly stated
               - Implicit ordering requirements
               - Shared resource conflicts
               - Race conditions in parallel execution
               
            2. **Resource Conflicts**:
               - Memory allocation overlaps
               - Database connection pool exhaustion
               - File system write conflicts
               - API rate limit violations
               
            3. **Interface Contract Gaps**:
               - Undefined data schemas between tasks
               - Missing error codes/handling specs
               - Ambiguous data type definitions
               - Unspecified null/missing data handling
               
            4. **Error Propagation Issues**:
               - No error boundaries defined
               - Missing rollback procedures
               - Unclear failure recovery paths
               - Cascading failure risks
               
            5. **Timing Edge Cases**:
               - Tasks with undefined timeouts
               - No handling for slow data sources
               - Missing retry logic specifications
               - Deadlock possibilities
            """,
    
    "code_implementation": """
            ### Code Implementation Critical Issues ###
            Identify these code-breaking problems:
            
            1. **Critical Bugs**:
               - Off-by-one errors in loops/indices
               - Null/undefined reference errors
               - Division by zero possibilities
               - Integer overflow risks
               - Floating point precision issues
               
            2. **Data Leakage Risks**:
               - Future information in features
               - Target variable contamination
               - Cross-validation data mixing
               - Test set information leakage
               
            3. **Performance Bottlenecks**:
               - O(n²) or worse algorithms
               - Unnecessary data copies
               - Missing vectorization opportunities
               - Database N+1 query problems
               - Memory leaks
               
            4. **Edge Case Handling**:
               - Empty dataset handling
               - Single observation scenarios
               - Extreme value handling
               - Missing data edge cases
               - Timezone boundary issues
               
            5. **Integration Failures**:
               - API contract violations
               - Data type mismatches
               - Schema incompatibilities
               - Missing error handling
               - Incorrect assumptions about inputs
            """,
    
    "experiment_execution": """
            ### Experiment Execution Critical Errors ###
            Check for these execution failures:
            
            1. **Missing Experiment Steps**:
               - Skipped preprocessing steps
               - Forgotten validation checks
               - Missing baseline comparisons
               - Incomplete parameter sweeps
               
            2. **Parameter Setting Errors**:
               - Wrong hyperparameters used
               - Incorrect random seeds
               - Missing configuration values
               - Environment variable errors
               
            3. **Data Loading Issues**:
               - Wrong data files loaded
               - Incorrect date ranges
               - Missing data filters
               - Data version mismatches
               
            4. **Result Storage Problems**:
               - Results not persisted
               - Overwriting previous results
               - Incomplete result sets
               - Missing metadata storage
               
            5. **Execution Environment Issues**:
               - Package version conflicts
               - Missing dependencies
               - Hardware/software mismatches
               - Resource exhaustion
            """,
    
    "results_extraction": """
            ### Results Extraction Critical Issues ###
            Identify these extraction problems:
            
            1. **Missing Required Outputs**:
               - Charts/tables from research plan missing
               - Key metrics not calculated
               - Statistical summaries incomplete
               - Comparison results absent
               
            2. **Aggregation Logic Errors**:
               - Incorrect averaging methods
               - Wrong time period groupings
               - Improper weighting schemes
               - Missing data handling errors
               
            3. **Visualization Errors**:
               - Axis scaling issues
               - Missing labels/legends
               - Incorrect chart types
               - Data misrepresentation
               
            4. **Calculation Mistakes**:
               - Wrong formulas used
               - Incorrect statistical tests
               - Precision/rounding errors
               - Unit conversion failures
               
            5. **Format/Export Issues**:
               - Incorrect file formats
               - Missing data exports
               - Corrupted outputs
               - Encoding problems
            """
}

# Senior validator context-specific prompts
SENIOR_VALIDATION_PROMPTS = {
    "research_plan": """
            ### META-VERIFICATION: REVIEW THE JUNIOR VALIDATOR'S CRITIQUE ###
            You are the Chief Validator reviewing the Junior's bug report. Your task is NOT to re-validate the entire plan.
            Your goal is to assess the QUALITY and VALIDITY of the Junior's findings.
            
            **1. REVIEW EACH FINDING FROM THE JUNIOR**:
            For each issue the Junior identified, determine:
               □ Is this a VALID concern or is the Junior being overly pedantic?
               □ Is this actually a CRITICAL ERROR or just a minor improvement?
               □ Did the Junior misunderstand the plan's approach?
               □ Is the Junior asking for unnecessary complexity?
               
            **2. FILTER OUT TRIVIAL ISSUES**:
            REJECT Junior's findings that are:
               - Obvious to expert practitioners (basic statistical knowledge)
               - Standard industry practices that don't need explicit stating
               - Overly academic requirements not needed for practical research
               - Pedantic formatting or documentation issues
               - "Nice to have" features presented as critical
               
            **3. VALIDATE CRITICAL ERRORS**:
            CONFIRM Junior's findings only if they are:
               - Genuine logical flaws that break the approach
               - Missing essential components for the task
               - Factual errors in methodology
               - Real implementation blockers
               
            **4. ADD YOUR OWN STRATEGIC ASSESSMENT**:
            Beyond the Junior's tactical checks, evaluate:
               - Does the plan address the actual business need?
               - Is the approach practical and actionable?
               - Are the deliverables what stakeholders need?
               - Is the scope appropriate for the timeline?
               
            **5. PRODUCE YOUR CURATED BUG REPORT**:
            Your output should:
               - List which Junior findings you ACCEPT (with reasoning)
               - List which Junior findings you REJECT (with reasoning)
               - Add any strategic issues the Junior missed
               - Provide a FINAL VERDICT that considers both tactical and strategic aspects
            
            Remember: You are the arbiter. Filter noise, keep signal.
            ### Comprehensive Research Plan Analysis ###
            Beyond the junior validator's findings, conduct deep analysis of:
            
            1. **Statistical Rigor & Power**:
               - Sample size adequacy for detecting alpha (power analysis)
               - Multiple hypothesis testing corrections (FDR, Bonferroni)
               - Out-of-sample validation methodology
               - Cross-validation scheme appropriateness
               - Statistical significance thresholds
               
            2. **Hypothesis Clarity**:
               - Precise, testable hypothesis statements
               - Clear null/alternative hypotheses
               - Economic rationale for each hypothesis
               - Prior probability assessments
               
            3. **Data Hygiene Protocols**:
               - Outlier detection and treatment methods
               - Missing data imputation strategies
               - Data quality scoring mechanisms
               - Cross-source validation procedures
               - Time zone alignment protocols
               
            4. **Missing Interesting Relationships**:
               - Cross-asset correlations worth exploring
               - Regime-dependent behaviors to investigate
               - Non-linear relationships to test
               - Interaction effects between factors
               - Lead-lag relationships
               
            5. **Experimental Design Robustness**:
               - Control group construction
               - Randomization procedures
               - Confounding variable identification
               - Robustness check specifications
               - Sensitivity analysis plans
               
            6. **Result Interpretation Framework**:
               - Economic significance vs statistical significance
               - Performance attribution methodology
               - Risk-adjusted return metrics
               - Implementation feasibility assessment
               - Transaction cost impact analysis
            """,
    
    "implementation_manifest": """
            ### Project Management Excellence Analysis ###
            Evaluate the implementation manifest for:
            
            1. **Parallelization Efficiency**:
               - EVERY opportunity for parallel execution identified
               - No artificial sequential dependencies
               - Optimal task granularity (not too fine, not too coarse)
               - Load balancing across parallel workers
               - Resource utilization optimization
               
            2. **Surgical Alignment Points**:
               - Crystal clear convergence specifications
               - Data schema alignment at merge points
               - Timestamp synchronization methods
               - Deduplication strategies defined
               - Conflict resolution procedures
               
            3. **Success Criteria Measurability**:
               - Quantifiable success metrics for each task
               - Automated validation procedures
               - Performance benchmarks specified
               - Quality gates clearly defined
               - Progress tracking mechanisms
               
            4. **Task Boundaries & Responsibilities**:
               - Clear input/output specifications
               - No overlapping responsibilities
               - Complete coverage of research plan
               - Explicit "must not do" constraints
               - Resource allocation clarity
               
            5. **Experiment Logging Structure**:
               - Comprehensive logging specifications
               - Structured format definitions
               - Metadata capture requirements
               - Reproducibility information
               - Performance metrics logging
               
            6. **Alignment with Research Plan**:
               - Every research requirement mapped to tasks
               - No missing experimental components
               - Data collection completeness
               - Analysis coverage verification
            """,
    
    "code_implementation": """
            ### Code Quality & Compliance Analysis ###
            Comprehensive evaluation of:
            
            1. **Orchestrator Success Criteria Compliance**:
               - Every success criterion explicitly addressed
               - Performance benchmarks achieved
               - Resource constraints respected
               - Output format exactly as specified
               - Integration points properly implemented
               
            2. **Interface Contract Adherence**:
               - Input validation against schema
               - Output format compliance
               - Error code implementation
               - Data type consistency
               - Null handling as specified
               
            3. **Statistical Implementation Correctness**:
               - Correct statistical test implementations
               - Proper hypothesis test setup
               - Accurate p-value calculations
               - Correct confidence intervals
               - Proper multiple testing corrections
               
            4. **Data Transformation Validity**:
               - Feature engineering correctness
               - Scaling/normalization appropriateness
               - Categorical encoding validity
               - Time series alignment accuracy
               - Missing data handling consistency
               
            5. **Integration Readiness**:
               - Clean interfaces with other components
               - Proper logging implementation
               - Error handling completeness
               - Documentation adequacy
               - Test coverage sufficiency
               
            6. **Performance & Efficiency**:
               - Vectorized operations where possible
               - Efficient data structures used
               - Memory usage optimization
               - Computation time within limits
               - Scalability considerations
            """,
    
    "experiment_execution": """
            ### Experimental Protocol Compliance ###
            Thorough analysis of:
            
            1. **Research Plan Protocol Adherence**:
               - Every specified experiment executed
               - Correct experimental design followed
               - Control conditions properly run
               - All parameter combinations tested
               - Robustness checks completed
               
            2. **Statistical Test Execution**:
               - Correct test statistics calculated
               - Proper degrees of freedom
               - Accurate p-value computation
               - Confidence intervals correct
               - Effect sizes calculated
               
            3. **Result Completeness**:
               - All required metrics computed
               - Performance across all periods
               - Risk metrics comprehensive
               - Attribution analysis complete
               - Sensitivity analysis done
               
            4. **Reproducibility Documentation**:
               - Complete environment specification
               - All parameters logged
               - Random seeds recorded
               - Data versions documented
               - Execution timestamps
               
            5. **Quality Control Checks**:
               - Sanity checks passed
               - Results within expected ranges
               - No numerical instabilities
               - Convergence achieved
               - Cross-validation completed
               
            6. **Journal Quality**:
               - Clear execution narrative
               - Issues and resolutions documented
               - Performance metrics tracked
               - Resource usage logged
               - Insights captured
            """,
    
    "results_extraction": """
            ### Results Extraction Completeness Analysis ###
            Comprehensive validation of:
            
            1. **Chief Researcher Question Coverage**:
               - Every research question answered
               - All hypotheses addressed
               - Required insights extracted
               - Secondary relationships analyzed
               - Unexpected findings highlighted
               
            2. **Statistical Summary Accuracy**:
               - Correct summary statistics
               - Proper significance reporting
               - Accurate effect sizes
               - Confidence intervals correct
               - Multiple testing adjustments applied
               
            3. **Result Interpretation Validity**:
               - Economic significance assessed
               - Statistical vs practical importance
               - Limitations clearly stated
               - Caveats properly noted
               - Alternative explanations considered
               
            4. **Presentation Quality**:
               - Clear, professional visualizations
               - Appropriate chart types
               - Effective use of tables
               - Logical flow of results
               - Executive summary quality
               
            5. **Data Integrity**:
               - Source data traced
               - Transformations documented
               - Calculations verifiable
               - Results reproducible
               - No data manipulation errors
               
            6. **Actionable Insights**:
               - Clear recommendations
               - Implementation considerations
               - Risk assessments included
               - Next steps identified
               - Practical applications noted
            """
}