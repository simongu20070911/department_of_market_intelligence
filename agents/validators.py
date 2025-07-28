# /department_of_market_intelligence/agents/validators.py
import asyncio
from typing import AsyncGenerator
from google.adk.agents import LlmAgent, BaseAgent, ParallelAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from ..tools.desktop_commander import desktop_commander_toolset
from .. import config
from ..utils.callbacks import ensure_end_of_output
from ..utils.model_loader import get_llm_model

def get_junior_validator_agent():
    # Use mock agent in dry run mode
    if config.DRY_RUN_MODE and config.DRY_RUN_SKIP_LLM:
        from ..tools.mock_llm_agent import create_mock_llm_agent
        return create_mock_llm_agent(name="Junior_Validator")
    
    # Get tools from the registry (supports both mock and real MCP)
    from ..tools.toolset_registry import toolset_registry
    desktop_commander_toolset = toolset_registry.get_desktop_commander_toolset()
    
    # Wrap in list if it's a real MCP toolset, mock tools are already a list
    if toolset_registry.is_using_real_mcp():
        tools = [desktop_commander_toolset]
    else:
        tools = desktop_commander_toolset
        
    return LlmAgent(
        model=get_llm_model(config.VALIDATOR_MODEL),
        name="Junior_Validator",
        instruction="""
        ### Persona ###
        You are a Junior Validator. Your sole focus is on identifying critical, show-stopping errors and potential edge cases. You are concise and to the point.
        Today's date is: {current_date?}

        ### Context & State ###
        You will be given the path to an artifact to validate in `state['artifact_to_validate']`.
        You will also be given the current validation version number in `state['validation_version']`.

        ### Task ###
        1.  Use the `read_file` tool to load the content of the artifact specified in {artifact_to_validate}.
        2.  Rigorously review the content for any glaring errors, logical fallacies, or unhandled edge cases.
        3.  If you find no critical issues, your critique should be a single sentence: "No critical issues found."
        4.  Use the `write_file` tool to save your critique to `outputs/junior_critique_v{validation_version}.md`.
        5.  State update will be handled automatically.

        ### Output Format ###
        You MUST end every response with "<end of output>".
        """,
        tools=tools,
        after_model_callback=ensure_end_of_output
    )

def get_senior_validator_agent():
    # Use mock agent in dry run mode
    if config.DRY_RUN_MODE and config.DRY_RUN_SKIP_LLM:
        from ..tools.mock_llm_agent import create_mock_llm_agent
        return create_mock_llm_agent(name="Senior_Validator")
    
    # Get tools from the registry (supports both mock and real MCP)
    from ..tools.toolset_registry import toolset_registry
    desktop_commander_toolset = toolset_registry.get_desktop_commander_toolset()
    
    # Wrap in list if it's a real MCP toolset, mock tools are already a list
    if toolset_registry.is_using_real_mcp():
        tools = [desktop_commander_toolset]
    else:
        tools = desktop_commander_toolset
        
    return LlmAgent(
        model=get_llm_model(config.VALIDATOR_MODEL),
        name="Senior_Validator",
        instruction="""
        ### Persona ###
        You are a Senior Validator. You provide detailed, constructive, and comprehensive analysis, building upon the junior validator's findings. Your judgment determines if a work product is ready.
        Today's date is: {current_date?}

        ### Context & State ###
        - Primary artifact to validate: {artifact_to_validate}
        - Junior validator's critique: {junior_critique_artifact}
        - Current validation version: {validation_version}

        ### Task ###
        1.  Use `read_file` to load both the primary artifact and the junior critique.
        2.  Synthesize the junior's findings with your own in-depth analysis. Assess the work for:
            - Methodological soundness and statistical rigor
            - Alignment with research goals and requirements
            - Overall quality and completeness
            - **For implementation manifests**: Project management excellence:
              * Maximum parallelization achieved
              * Clear interface contracts and stitching points
              * Efficient resource utilization
              * No artificial sequential bottlenecks
        3.  Use `write_file` to save your comprehensive critique to `outputs/senior_critique_v{validation_version}.md`.
        4.  Update the session state: `state['senior_critique_artifact'] = 'outputs/senior_critique_v{validation_version}.md'`.
        5.  **Crucially, you must make a final judgment.** Based on your analysis, set the session state key `state['validation_status']` to one of these exact string values:
           - 'approved': Work is satisfactory and ready to proceed
           - 'rejected': Work needs refinement but can be fixed in current loop  
           - 'critical_error': Unresolvable error requiring replanning/recoding (escalates to orchestrator)

        ### Output Format ###
        You MUST end every response with "<end of output>".
        """,
        tools=tools,
        after_model_callback=ensure_end_of_output
    )

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


def get_parallel_final_validation_agent():
    """Create a parallel final validation agent for thorough multi-perspective review."""
    return ParallelFinalValidationAgent(name="ParallelFinalValidation")


class ParallelFinalValidationAgent(BaseAgent):
    """Runs multiple validators in parallel for comprehensive final validation."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._parallel_validators = None
    
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        if self._parallel_validators is None:
            # Create multiple specialized validators for parallel execution
            validators = []
            
            for i in range(config.PARALLEL_VALIDATION_SAMPLES):
                # Create different types of validators for comprehensive coverage
                if i == 0:
                    # Statistical rigor validator
                    validators.append(self._create_statistical_validator(i))
                elif i == 1:
                    # Data hygiene validator
                    validators.append(self._create_data_hygiene_validator(i))
                elif i == 2:
                    # Methodology validator
                    validators.append(self._create_methodology_validator(i))
                elif i == 3:
                    # Efficiency and parallelization validator
                    validators.append(self._create_efficiency_validator(i))
                else:
                    # General critical validator
                    validators.append(self._create_general_validator(i))
            
            self._parallel_validators = ParallelAgent(
                name="ParallelValidatorGroup",
                sub_agents=validators
            )
        
        print(f"PARALLEL FINAL VALIDATION: Running {config.PARALLEL_VALIDATION_SAMPLES} validators in parallel...")
        
        # Track validation results
        validation_results = []
        
        # Execute all validators in parallel
        async for event in self._parallel_validators.run_async(ctx):
            yield event
        
        # Analyze parallel validation results
        print("PARALLEL FINAL VALIDATION: Analyzing results from all validators...")
        
        # Check if any critical issues were found
        critical_issues_found = ctx.session.state.get('parallel_validation_critical_issues', [])
        
        if critical_issues_found:
            print(f"PARALLEL FINAL VALIDATION: {len(critical_issues_found)} critical issues found")
            ctx.session.state['validation_status'] = 'critical_error'
            # Store consolidated issues for review
            ctx.session.state['consolidated_validation_issues'] = critical_issues_found
        else:
            print("PARALLEL FINAL VALIDATION: All validators passed - proceeding")
            ctx.session.state['validation_status'] = 'approved'
        
        yield Event(
            author=self.name,
            actions=EventActions()
        )
    
    def _create_statistical_validator(self, index: int) -> BaseAgent:
        """Create a validator focused on statistical rigor."""
        if config.DRY_RUN_MODE and config.DRY_RUN_SKIP_LLM:
            from ..tools.mock_llm_agent import create_mock_llm_agent
            return create_mock_llm_agent(name=f"StatisticalValidator_{index}")
        
        tools = self._get_tools()
        
        return LlmAgent(
            model=get_llm_model(config.VALIDATOR_MODEL),
            name=f"StatisticalValidator_{index}",
            instruction="""
            ### Persona ###
            You are a Statistical Rigor Validator specializing in quantitative finance research methodology.
            Your focus is on statistical significance, sample sizes, hypothesis testing, and experimental design.
            Today's date is: {current_date?}

            ### Context & State ###
            Artifact to validate: {artifact_to_validate}
            Current validation version: {validation_version}

            ### Task ###
            1. Read the artifact using `read_file` tool
            2. Focus EXCLUSIVELY on statistical rigor:
               - Sample size adequacy and power analysis
               - Hypothesis testing methodology  
               - Multiple testing corrections
               - Statistical significance thresholds
               - Data distribution assumptions
               - Backtesting methodology validity
               - Risk-adjusted performance metrics
            3. If you find CRITICAL statistical issues, write them to `outputs/parallel_validation_statistical_v{validation_version}.md`
            4. If no critical statistical issues: write "No critical statistical issues found."

            ### Output Format ###
            End with "<end of output>".
            """,
            tools=tools,
            after_model_callback=ensure_end_of_output
        )
    
    def _create_data_hygiene_validator(self, index: int) -> BaseAgent:
        """Create a validator focused on data quality and hygiene."""
        if config.DRY_RUN_MODE and config.DRY_RUN_SKIP_LLM:
            from ..tools.mock_llm_agent import create_mock_llm_agent
            return create_mock_llm_agent(name=f"DataHygieneValidator_{index}")
        
        tools = self._get_tools()
        
        return LlmAgent(
            model=get_llm_model(config.VALIDATOR_MODEL),
            name=f"DataHygieneValidator_{index}",
            instruction="""
            ### Persona ###
            You are a Data Hygiene Validator specializing in data quality and integrity for quantitative research.
            Your focus is on data cleanliness, completeness, and reliability.
            Today's date is: {current_date?}

            ### Context & State ###
            Artifact to validate: {artifact_to_validate}
            Current validation version: {validation_version}

            ### Task ###
            1. Read the artifact using `read_file` tool
            2. Focus EXCLUSIVELY on data hygiene:
               - Data cleaning procedures
               - Missing data handling strategies
               - Outlier detection and treatment
               - Data source reliability and consistency
               - Temporal data alignment
               - Corporate actions and splits handling
               - Survivorship bias prevention
            3. If you find CRITICAL data hygiene issues, write them to `outputs/parallel_validation_data_v{validation_version}.md`
            4. If no critical data issues: write "No critical data hygiene issues found."

            ### Output Format ###
            End with "<end of output>".
            """,
            tools=tools,
            after_model_callback=ensure_end_of_output
        )
    
    def _create_methodology_validator(self, index: int) -> BaseAgent:
        """Create a validator focused on research methodology."""
        if config.DRY_RUN_MODE and config.DRY_RUN_SKIP_LLM:
            from ..tools.mock_llm_agent import create_mock_llm_agent
            return create_mock_llm_agent(name=f"MethodologyValidator_{index}")
        
        tools = self._get_tools()
        
        return LlmAgent(
            model=get_llm_model(config.VALIDATOR_MODEL),
            name=f"MethodologyValidator_{index}",
            instruction="""
            ### Persona ###
            You are a Research Methodology Validator specializing in quantitative finance research design.
            Your focus is on experimental design, controls, and methodological soundness.
            Today's date is: {current_date?}

            ### Context & State ###
            Artifact to validate: {artifact_to_validate}
            Current validation version: {validation_version}

            ### Task ###
            1. Read the artifact using `read_file` tool
            2. Focus EXCLUSIVELY on methodology:
               - Experimental design validity
               - Control group appropriateness
               - Factor model specification
               - Risk model completeness
               - Benchmark selection rationale
               - Performance attribution methodology
               - Transaction cost modeling
            3. If you find CRITICAL methodology issues, write them to `outputs/parallel_validation_method_v{validation_version}.md`
            4. If no critical methodology issues: write "No critical methodology issues found."

            ### Output Format ###
            End with "<end of output>".
            """,
            tools=tools,
            after_model_callback=ensure_end_of_output
        )
    
    def _create_efficiency_validator(self, index: int) -> BaseAgent:
        """Create a validator focused on parallelization efficiency and project management."""
        if config.DRY_RUN_MODE and config.DRY_RUN_SKIP_LLM:
            from ..tools.mock_llm_agent import create_mock_llm_agent
            return create_mock_llm_agent(name=f"EfficiencyValidator_{index}")
        
        tools = self._get_tools()
        
        return LlmAgent(
            model=get_llm_model(config.VALIDATOR_MODEL),
            name=f"EfficiencyValidator_{index}",
            instruction="""
            ### Persona ###
            You are an Efficiency and Parallelization Validator for quantitative finance research pipelines.
            Your focus is on maximizing computational efficiency and identifying missed parallelization opportunities.
            Today's date is: {current_date?}

            ### Context & State ###
            Artifact to validate: {artifact_to_validate}
            Current validation version: {validation_version}

            ### Task ###
            1. Read the artifact using `read_file` tool
            2. If validating an implementation manifest, focus EXCLUSIVELY on:
               - MISSED PARALLELIZATION: Tasks that could run in parallel but have unnecessary dependencies
               - INEFFICIENT SEQUENCING: Sequential chains that could be parallel streams
               - MISSING STITCHING POINTS: Parallel streams without clear convergence definitions
               - WEAK INTERFACE CONTRACTS: Missing or vague data schemas between tasks
               - RESOURCE WASTE: Tasks not utilizing available parallel compute
               - BOTTLENECKS: Single tasks that block many parallel streams
               - OVER-ENGINEERING: Unnecessarily complex task decomposition
               
            3. CRITICAL issues to flag:
               - Data fetching from different sources NOT parallelized
               - Feature engineering for independent features NOT parallelized  
               - Model training/backtesting for different configs NOT parallelized
               - Missing `parallel_group` assignments for concurrent tasks
               - Missing `interface_contract` specifications at convergence points
               - Dependencies based on "logical order" rather than data flow
               - More than 3 sequential tasks where parallelization is possible
               
            4. If you find CRITICAL efficiency issues, write them to `outputs/parallel_validation_efficiency_v{validation_version}.md`
            5. If no critical efficiency issues: write "No critical efficiency issues found."

            ### Output Format ###
            End with "<end of output>".
            """,
            tools=tools,
            after_model_callback=ensure_end_of_output
        )
    
    def _create_general_validator(self, index: int) -> BaseAgent:
        """Create a general purpose validator for comprehensive review."""
        if config.DRY_RUN_MODE and config.DRY_RUN_SKIP_LLM:
            from ..tools.mock_llm_agent import create_mock_llm_agent
            return create_mock_llm_agent(name=f"GeneralValidator_{index}")
        
        tools = self._get_tools()
        
        return LlmAgent(
            model=get_llm_model(config.VALIDATOR_MODEL),
            name=f"GeneralValidator_{index}",
            instruction="""
            ### Persona ###
            You are a Comprehensive Validator for quantitative finance research.
            Your focus is on overall coherence, completeness, and critical thinking.
            Today's date is: {current_date?}

            ### Context & State ###
            Artifact to validate: {artifact_to_validate}
            Current validation version: {validation_version}

            ### Task ###
            1. Read the artifact using `read_file` tool
            2. Focus on comprehensive review:
               - Logical consistency and flow
               - Completeness of analysis
               - Missing critical considerations
               - Implementation feasibility
               - Resource requirements
               - Timeline realism
               - Result interpretation validity
            3. If you find CRITICAL general issues, write them to `outputs/parallel_validation_general_v{validation_version}.md`
            4. If no critical general issues: write "No critical general issues found."

            ### Output Format ###
            End with "<end of output>".
            """,
            tools=tools,
            after_model_callback=ensure_end_of_output
        )
    
    def _get_tools(self):
        """Get appropriate tools based on execution mode."""
        if config.DRY_RUN_MODE:
            from ..tools.mock_tools import mock_desktop_commander_toolset
            return mock_desktop_commander_toolset
        else:
            return [desktop_commander_toolset]