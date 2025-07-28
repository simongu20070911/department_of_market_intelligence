# /department_of_market_intelligence/agents/validators_context_aware.py
"""Context-aware validators that adapt their prompts based on what they're validating."""

import asyncio
from typing import AsyncGenerator, Dict, Any
from google.adk.agents import LlmAgent, BaseAgent, ParallelAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from ..tools.desktop_commander import desktop_commander_toolset
from .. import config
from ..utils.callbacks import ensure_end_of_output
from ..utils.model_loader import get_llm_model


# Validation context types
VALIDATION_CONTEXTS = {
    "research_plan": "Research Plan from Chief Researcher",
    "implementation_manifest": "Implementation Manifest from Orchestrator", 
    "code_implementation": "Code Implementation from Parallel Coders",
    "experiment_execution": "Experiment Execution Journal",
    "results_extraction": "Results Extraction Plan/Code"
}


def get_validation_context_prompt(context_type: str, role: str) -> Dict[str, str]:
    """Get context-specific prompts for validators based on what they're validating."""
    
    prompts = {
        "research_plan": {
            "junior": """
            ### Specific Focus for Research Plan Validation ###
            As you review this research plan, focus on these CRITICAL edge cases and errors:
            
            1. **Data Availability Edge Cases**:
               - Historical data gaps or limitations
               - Survivorship bias in universe selection
               - Corporate actions handling (splits, dividends, mergers)
               - Data vendor inconsistencies
               - Weekend/holiday data handling
               
            2. **Statistical Assumption Failures**:
               - Stationarity assumptions that might break
               - Normal distribution assumptions for fat-tailed markets
               - Independence assumptions in correlated markets
               - Sample size insufficiency for proposed tests
               
            3. **Market Regime Dependencies**:
               - Strategy performance in different volatility regimes
               - Behavior during market crashes/rallies
               - Regulatory change impacts
               - Liquidity regime considerations
               
            4. **Lookahead Bias Risks**:
               - Point-in-time data availability
               - Earnings announcement timing
               - Index reconstitution knowledge
               - Economic data revision handling
               
            5. **Computational Edge Cases**:
               - Numerical precision for small probabilities
               - Matrix singularity in factor models
               - Optimization convergence issues
               - Backtesting speed/memory constraints
            """,
            
            "senior": """
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
            """
        },
        
        "implementation_manifest": {
            "junior": """
            ### Critical Issues in Implementation Manifest ###
            Focus on these potential show-stoppers:
            
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
            
            "senior": """
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
            """
        },
        
        "code_implementation": {
            "junior": """
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
            
            "senior": """
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
            """
        },
        
        "experiment_execution": {
            "junior": """
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
            
            "senior": """
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
            """
        },
        
        "results_extraction": {
            "junior": """
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
            """,
            
            "senior": """
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
    }
    
    return prompts.get(context_type, {}).get(role, "")


def get_junior_validator_agent():
    """Create a context-aware junior validator."""
    # Use mock agent in dry run mode
    if config.DRY_RUN_MODE and config.DRY_RUN_SKIP_LLM:
        from ..tools.mock_llm_agent import create_mock_llm_agent
        return create_mock_llm_agent(name="Junior_Validator")
    
    # Use mock tools in dry run mode
    if config.DRY_RUN_MODE:
        from ..tools.mock_tools import mock_desktop_commander_toolset
        tools = mock_desktop_commander_toolset
    else:
        tools = desktop_commander_toolset
        
    return LlmAgent(
        model=get_llm_model(config.VALIDATOR_MODEL),
        name="Junior_Validator",
        instruction="""
        ### Persona ###
        You are a Junior Validator for ULTRATHINK_QUANTITATIVEMarketAlpha. Your sole focus is on identifying critical, show-stopping errors and potential edge cases. You are concise and direct.
        Today's date is: {current_date?}

        ### Context & State ###
        - Artifact to validate: {artifact_to_validate}
        - Validation context: {validation_context?}
        - Validation version: {validation_version}

        ### Core Task ###
        1. Use the `read_file` tool to load the artifact specified in {artifact_to_validate}
        2. Identify the validation context from {validation_context?} to understand what type of artifact you're validating
        3. Apply context-specific validation based on the artifact type:

        {context_specific_prompt}

        ### Output Requirements ###
        - If you find critical issues, list them clearly and concisely
        - For each issue, explain WHY it's critical and its potential impact
        - If no critical issues found, write: "No critical issues found."
        - Use `write_file` to save your critique to `outputs/junior_critique_v{validation_version}.md`
        - Include a section "Key Files Reviewed:" listing important files you examined

        ### Output Format ###
        You MUST end every response with "<end of output>".
        """,
        tools=tools,
        after_model_callback=ensure_end_of_output
    )


def get_senior_validator_agent():
    """Create a context-aware senior validator with recursive context loading capability."""
    # Use mock agent in dry run mode
    if config.DRY_RUN_MODE and config.DRY_RUN_SKIP_LLM:
        from ..tools.mock_llm_agent import create_mock_llm_agent
        return create_mock_llm_agent(name="Senior_Validator")
    
    # Use mock tools in dry run mode
    if config.DRY_RUN_MODE:
        from ..tools.mock_tools import mock_desktop_commander_toolset
        tools = mock_desktop_commander_toolset
    else:
        tools = desktop_commander_toolset
        
    return LlmAgent(
        model=get_llm_model(config.VALIDATOR_MODEL),
        name="Senior_Validator",
        instruction="""
        ### Persona ###
        You are a Senior Validator for ULTRATHINK_QUANTITATIVEMarketAlpha. You provide detailed, constructive, and comprehensive analysis. Your judgment determines if work is ready to proceed.
        Today's date is: {current_date?}

        ### Context & State ###
        - Primary artifact: {artifact_to_validate}
        - Junior critique: {junior_critique_artifact}
        - Validation context: {validation_context?}
        - Validation version: {validation_version}

        ### Core Task ###
        1. Load and analyze both the primary artifact and junior critique using `read_file`
        2. Identify the validation context to understand what you're validating
        3. Apply deep, context-specific analysis based on the artifact type:

        {context_specific_prompt}

        ### Recursive Context Loading ###
        You have the ability to recursively load additional context:
        - Use `list_directory` to explore relevant directories
        - Use `read_file` to examine dependencies, related files, or previous versions
        - Use `search_code` to find implementations or definitions
        - Build a complete understanding of the work in its full context

        ### Synthesis & Judgment ###
        1. Synthesize junior validator findings with your comprehensive analysis
        2. Write detailed critique to `outputs/senior_critique_v{validation_version}.md`
        3. Include sections:
           - "Junior Validator Findings Addressed"
           - "Additional Critical Analysis" 
           - "Recommendations for Improvement"
           - "Key Files Reviewed" (list all files examined)
           
        4. Make final judgment - set `state['validation_status']` to:
           - 'approved': Work meets all quality standards
           - 'rejected': Needs refinement but fixable
           - 'critical_error': Fundamental issues requiring major rework

        ### Decision Criteria ###
        - For 'approved': No critical issues, minor improvements optional
        - For 'rejected': Issues that must be fixed but approach is sound
        - For 'critical_error': Fundamental flaws in approach or execution

        ### Output Format ###
        You MUST end every response with "<end of output>".
        """,
        tools=tools,
        after_model_callback=ensure_end_of_output
    )


def create_specialized_parallel_validator(validator_type: str, index: int) -> BaseAgent:
    """Create a specialized validator for parallel validation based on context."""
    
    if config.DRY_RUN_MODE and config.DRY_RUN_SKIP_LLM:
        from ..tools.mock_llm_agent import create_mock_llm_agent
        return create_mock_llm_agent(name=f"{validator_type}_{index}")
    
    tools = desktop_commander_toolset if not config.DRY_RUN_MODE else None
    
    validator_configs = {
        "research_plan": {
            "statistical": {
                "name": "StatisticalRigorValidator",
                "focus": """
                Focus EXCLUSIVELY on statistical methodology:
                - Hypothesis test appropriateness (t-test vs Mann-Whitney, etc.)
                - Sample size and power calculations
                - Multiple testing correction methods
                - Assumption validation procedures
                - Effect size interpretation plans
                - Confidence interval specifications
                - Time series stationarity tests
                - Cross-sectional independence tests
                """,
            },
            "data": {
                "name": "DataQualityValidator", 
                "focus": """
                Focus EXCLUSIVELY on data quality:
                - Data source reliability assessments
                - Missing data handling strategies
                - Outlier detection methodologies
                - Survivorship bias prevention
                - Point-in-time data procedures
                - Corporate action adjustments
                - Vendor reconciliation plans
                - Data versioning strategies
                """,
            },
            "market": {
                "name": "MarketStructureValidator",
                "focus": """
                Focus EXCLUSIVELY on market considerations:
                - Market microstructure effects
                - Liquidity considerations
                - Transaction cost modeling
                - Market impact estimation
                - Regulatory regime handling
                - Cross-market consistency
                - Trading hour adjustments
                - Holiday calendar handling
                """,
            }
        },
        "implementation_manifest": {
            "parallelization": {
                "name": "ParallelizationValidator",
                "focus": """
                Focus EXCLUSIVELY on parallelization:
                - Tasks that could run in parallel but don't
                - Unnecessary sequential dependencies
                - Resource utilization optimization
                - Load balancing across workers
                - Bottleneck identification
                - Parallel group assignments
                - Convergence point efficiency
                - Missing parallel opportunities
                """,
            },
            "interfaces": {
                "name": "InterfaceContractValidator",
                "focus": """
                Focus EXCLUSIVELY on interfaces:
                - Data schema completeness
                - Type specifications clarity
                - Error code definitions
                - Validation rule presence
                - Null handling specifications
                - Schema version compatibility
                - Format conversion needs
                - Integration test points
                """,
            },
            "alignment": {
                "name": "PlanAlignmentValidator",
                "focus": """
                Focus EXCLUSIVELY on plan alignment:
                - Research requirements coverage
                - Missing experimental components
                - Success criteria mapping
                - Output completeness
                - Timeline feasibility
                - Resource adequacy
                - Dependency accuracy
                - Risk mitigation presence
                """,
            }
        }
    }
    
    # Get the validation context from state (will be set by the workflow)
    validation_context = "{validation_context?}"
    config_key = validation_context.split("_")[0] if validation_context else "research"
    
    validator_config = validator_configs.get(config_key, validator_configs["research_plan"])
    validator_info = list(validator_config.values())[index % len(validator_config)]
    
    return LlmAgent(
        model=get_llm_model(config.VALIDATOR_MODEL),
        name=f"{validator_info['name']}_{index}",
        instruction=f"""
        ### Persona ###
        You are a {validator_info['name']} for ULTRATHINK_QUANTITATIVEMarketAlpha parallel validation.
        Today's date is: {{current_date?}}

        ### Context & State ###
        Artifact to validate: {{artifact_to_validate}}
        Validation context: {{validation_context?}}
        Validation version: {{validation_version}}

        ### Specialized Focus ###
        {validator_info['focus']}

        ### Task ###
        1. Read the artifact using `read_file`
        2. Apply your specialized lens to identify issues
        3. ONLY report CRITICAL issues in your focus area
        4. Write findings to `outputs/parallel_validation_{validator_type.lower()}_v{{validation_version}}.md`
        5. If no critical issues in your domain: "No critical {validator_type.lower()} issues found."

        ### Output Format ###
        End with "<end of output>".
        """,
        tools=tools,
        after_model_callback=ensure_end_of_output
    )


# Update the ParallelFinalValidationAgent to use context-aware validators
class ParallelFinalValidationAgent(BaseAgent):
    """Context-aware parallel validation agent."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._parallel_validators = None
    
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        # Get validation context from state
        validation_context = ctx.session.state.get('validation_context', 'research_plan')
        
        if self._parallel_validators is None:
            validators = []
            
            # Create specialized validators based on context
            for i in range(config.PARALLEL_VALIDATION_SAMPLES):
                validator = create_specialized_parallel_validator(
                    validator_type=self._get_validator_type(validation_context, i),
                    index=i
                )
                validators.append(validator)
            
            self._parallel_validators = ParallelAgent(
                name="ParallelValidatorGroup",
                sub_agents=validators
            )
        
        print(f"PARALLEL VALIDATION: Running {config.PARALLEL_VALIDATION_SAMPLES} specialized validators for {validation_context}")
        
        # Execute validators in parallel
        async for event in self._parallel_validators.run_async(ctx):
            yield event
        
        # Analyze results
        critical_issues = self._analyze_validation_results(ctx)
        
        if critical_issues:
            print(f"PARALLEL VALIDATION: {len(critical_issues)} critical issues found")
            ctx.session.state['validation_status'] = 'critical_error'
            ctx.session.state['consolidated_validation_issues'] = critical_issues
        else:
            print("PARALLEL VALIDATION: All validators passed")
            ctx.session.state['validation_status'] = 'approved'
        
        yield Event(
            author=self.name,
            actions=EventActions()
        )
    
    def _get_validator_type(self, validation_context: str, index: int) -> str:
        """Get validator type based on context and index."""
        context_validators = {
            "research_plan": ["statistical", "data", "market", "methodology", "general"],
            "implementation_manifest": ["parallelization", "interfaces", "alignment", "efficiency", "general"],
            "code_implementation": ["bugs", "performance", "integration", "statistics", "general"],
            "experiment_execution": ["protocol", "completeness", "quality", "reproducibility", "general"],
            "results_extraction": ["coverage", "accuracy", "presentation", "insights", "general"]
        }
        
        validators = context_validators.get(validation_context, ["general"])
        return validators[index % len(validators)]
    
    def _analyze_validation_results(self, ctx: InvocationContext) -> list:
        """Analyze validation results from all parallel validators."""
        # Collect issues from state or analyze output files
        # This is simplified - in reality would parse validator outputs
        return ctx.session.state.get('parallel_validation_critical_issues', [])


# This is not an LLM agent. It's a simple control-flow agent.
class MetaValidatorCheckAgent(BaseAgent):
    """Checks the state for 'validation_status' and escalates based on the status."""
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        status = ctx.session.state.get("validation_status", "rejected")
        
        if status == "approved":
            print(f"META VALIDATOR: Status '{status}' - proceeding to next phase")
            should_escalate = True
        elif status == "critical_error":
            print(f"META VALIDATOR: Status '{status}' - escalating for replanning")
            # Set execution_status to trigger replanning at root level
            ctx.session.state['execution_status'] = 'critical_error'
            should_escalate = True
        else:  # rejected
            print(f"META VALIDATOR: Status '{status}' - continuing refinement loop")
            should_escalate = False
        
        # 'escalate=True' is the signal for a LoopAgent to terminate.
        yield Event(
            author=self.name,
            actions=EventActions(escalate=should_escalate)
        )
        # This is required for async generators, even if there's no real async work.
        await asyncio.sleep(0)


# Export the context-aware validator functions
def get_context_aware_validators():
    """Get all context-aware validators."""
    return {
        'junior': get_junior_validator_agent,
        'senior': get_senior_validator_agent,
        'parallel': ParallelFinalValidationAgent,
        'meta_check': MetaValidatorCheckAgent
    }