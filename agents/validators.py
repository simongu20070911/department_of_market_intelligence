# /department_of_market_intelligence/agents/validators.py
"""Context-aware validators that adapt their prompts based on what they're validating."""

import asyncio
from typing import AsyncGenerator, Dict, Any
from google.adk.agents import LlmAgent, BaseAgent, ParallelAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from .. import config
from ..utils.model_loader import get_llm_model
from google.adk.agents.llm_agent import InstructionProvider, ReadonlyContext
from ..prompts.definitions.validators import (
    JUNIOR_VALIDATOR_INSTRUCTIONS,
    SENIOR_VALIDATOR_INSTRUCTIONS
)
from ..prompts.components.contexts import (
    VALIDATION_CONTEXTS,
    JUNIOR_VALIDATION_PROMPTS,
    SENIOR_VALIDATION_PROMPTS
)


# Note: VALIDATION_CONTEXTS is imported from prompts/definitions/validators.py


def get_validation_context_prompt(context_type: str, role: str) -> str:
    """Get context-specific prompts for validators based on what they're validating."""
    if role == "junior":
        return JUNIOR_VALIDATION_PROMPTS.get(context_type, "")
    elif role == "senior":
        return SENIOR_VALIDATION_PROMPTS.get(context_type, "")
    return ""


def get_junior_validator_agent():
    """Create a context-aware junior validator."""
    # Only use mock agent in actual dry_run mode with LLM skipping
    if config.EXECUTION_MODE == "dry_run" and config.DRY_RUN_SKIP_LLM:
        from ..tools.mock_llm_agent import create_mock_llm_agent
        return create_mock_llm_agent(name="Junior_Validator")
    
    # Use centralized tool factory instead of duplicating logic
    from ..utils.tool_factory import create_agent_tools
    tools = create_agent_tools("Junior_Validator")
        
    def instruction_provider(ctx: ReadonlyContext) -> str:
        context_type = ctx.state.get("validation_context", "research_plan")
        return JUNIOR_VALIDATOR_INSTRUCTIONS.get(context_type, JUNIOR_VALIDATOR_INSTRUCTIONS["research_plan"])

    return LlmAgent(
        model=get_llm_model(config.VALIDATOR_MODEL),
        name="Junior_Validator",
        instruction=instruction_provider,
        tools=tools
    )


def get_senior_validator_agent():
    """Create a context-aware senior validator with recursive context loading capability."""
    # Only use mock agent in actual dry_run mode with LLM skipping
    if config.EXECUTION_MODE == "dry_run" and config.DRY_RUN_SKIP_LLM:
        from ..tools.mock_llm_agent import create_mock_llm_agent
        return create_mock_llm_agent(name="Senior_Validator")
    
    # Use centralized tool factory instead of duplicating logic
    from ..utils.tool_factory import create_agent_tools
    tools = create_agent_tools("Senior_Validator")
        
    def instruction_provider(ctx: ReadonlyContext) -> str:
        context_type = ctx.state.get("validation_context", "research_plan")
        return SENIOR_VALIDATOR_INSTRUCTIONS.get(context_type, SENIOR_VALIDATOR_INSTRUCTIONS["research_plan"])

    return LlmAgent(
        model=get_llm_model(config.VALIDATOR_MODEL),
        name="Senior_Validator",
        instruction=instruction_provider,
        tools=tools
    )


def create_specialized_parallel_validator(validator_type: str, index: int) -> BaseAgent:
    """Create a specialized validator for parallel validation based on context."""
    
    # Only use mock agent in actual dry_run mode with LLM skipping
    if config.EXECUTION_MODE == "dry_run" and config.DRY_RUN_SKIP_LLM:
        from ..tools.mock_llm_agent import create_mock_llm_agent
        return create_mock_llm_agent(name=f"{validator_type}_{index}")
    
    # Use centralized tool factory
    from ..utils.tool_factory import create_agent_tools
    tools = create_agent_tools(f"{validator_type}_{index}")
    
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
    
    instruction_template = f"""
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
        4. Write findings to `{{outputs_dir}}/parallel_validation_{validator_type.lower()}_v{{validation_version}}.md`
        5. If no critical issues in your domain: "No critical {validator_type.lower()} issues found."

        ### Output Format ###
        End with "<end of output>".
        """

    def instruction_provider(ctx: ReadonlyContext) -> str:
        # Use the actual task_id from the session (consistent with root workflow default)
        task_id = ctx.state.get("task_id", "research_session")
        outputs_dir = config.get_outputs_dir(task_id)
        return instruction_template.replace("{outputs_dir}", outputs_dir)

    return LlmAgent(
        model=get_llm_model(config.VALIDATOR_MODEL),
        name=f"{validator_info['name']}_{index}",
        instruction=instruction_provider,
        tools=tools
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
        if ctx.session.state.get('validation_status') == 'critical_error':
            return ctx.session.state.get('consolidated_validation_issues', [])
        return []


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
            # Reset the validation status so that the loop can continue
            ctx.session.state["validation_status"] = None
        
        # 'escalate=True' is the signal for a LoopAgent to terminate.
        yield Event(
            author=self.name,
            actions=EventActions(escalate=should_escalate)
        )
        # This is required for async generators, even if there's no real async work.
        await asyncio.sleep(0)


def get_parallel_final_validation_agent():
    """Get parallel final validation agent instance."""
    return ParallelFinalValidationAgent(name="ParallelFinalValidation")


# Export the context-aware validator functions
def get_context_aware_validators():
    """Get all context-aware validators."""
    return {
        'junior': get_junior_validator_agent,
        'senior': get_senior_validator_agent,
        'parallel': ParallelFinalValidationAgent,
        'meta_check': MetaValidatorCheckAgent
    }