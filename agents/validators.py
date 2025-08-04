# /department_of_market_intelligence/agents/validators.py
"""Context-aware validators that adapt their prompts based on what they're validating."""

import asyncio
import os
import re
from typing import AsyncGenerator, Dict, Any, Optional
from google.adk.agents import LlmAgent, BaseAgent, ParallelAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from .. import config
from ..utils.model_loader import get_llm_model
from ..utils.callbacks import ensure_end_of_output
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


# Cache for validator agents to maintain state within a single refinement loop.
_validator_agent_cache: Dict[str, BaseAgent] = {}

def clear_validator_cache():
    """Clear the validator agent cache to ensure fresh instances for new refinement loops."""
    global _validator_agent_cache
    if _validator_agent_cache:
        print("🔄 Clearing validator agent cache for new refinement cycle.")
        _validator_agent_cache.clear()


# Note: VALIDATION_CONTEXTS is imported from prompts/definitions/validators.py


def get_validation_context_prompt(context_type: str, role: str) -> str:
    """Get context-specific prompts for validators based on what they're validating."""
    if role == "junior":
        return JUNIOR_VALIDATION_PROMPTS.get(context_type, "")
    elif role == "senior":
        return SENIOR_VALIDATION_PROMPTS.get(context_type, "")
    return ""


def get_junior_validator_agent():
    """Create a context-aware junior validator, using a cache for statefulness within a loop."""
    agent_name = "Junior_Validator"
    if agent_name in _validator_agent_cache:
        return _validator_agent_cache[agent_name]

    # Only use mock agent in actual dry_run mode with LLM skipping
    if config.EXECUTION_MODE == "dry_run" and config.DRY_RUN_SKIP_LLM:
        from ..tools.mock_llm_agent import create_mock_llm_agent
        agent = create_mock_llm_agent(name=agent_name)
        _validator_agent_cache[agent_name] = agent
        return agent
    
    # Use the centralized toolset registry
    from ..tools.toolset_registry import toolset_registry
    desktop_commander_toolset = toolset_registry.get_desktop_commander_toolset()
    
    # Wrap in list if it's a real MCP toolset, mock tools are already a list
    if toolset_registry.is_using_real_mcp():
        tools = [desktop_commander_toolset]
    else:
        tools = desktop_commander_toolset
        
    def instruction_provider(ctx: ReadonlyContext) -> str:
        from ..prompts.builder import inject_template_variables_with_context_preloading
        context_type = ctx.state.get("validation_context", "research_plan")
        base_instruction = JUNIOR_VALIDATOR_INSTRUCTIONS.get(context_type, JUNIOR_VALIDATOR_INSTRUCTIONS["research_plan"])
        return inject_template_variables_with_context_preloading(base_instruction, ctx, "Junior_Validator")

    agent = LlmAgent(
        model=get_llm_model(config.VALIDATOR_MODEL),
        name=agent_name,
        instruction=instruction_provider,
        tools=tools,
        after_model_callback=ensure_end_of_output
    )
    _validator_agent_cache[agent_name] = agent
    return agent


def get_senior_validator_agent():
    """Create a context-aware senior validator, using a cache for statefulness within a loop."""
    agent_name = "Senior_Validator"
    if agent_name in _validator_agent_cache:
        return _validator_agent_cache[agent_name]

    # Only use mock agent in actual dry_run mode with LLM skipping
    if config.EXECUTION_MODE == "dry_run" and config.DRY_RUN_SKIP_LLM:
        from ..tools.mock_llm_agent import create_mock_llm_agent
        agent = create_mock_llm_agent(name=agent_name)
        _validator_agent_cache[agent_name] = agent
        return agent
    
    # Use the centralized toolset registry
    from ..tools.toolset_registry import toolset_registry
    desktop_commander_toolset = toolset_registry.get_desktop_commander_toolset()
    
    # Wrap in list if it's a real MCP toolset, mock tools are already a list
    if toolset_registry.is_using_real_mcp():
        tools = [desktop_commander_toolset]
    else:
        tools = desktop_commander_toolset
        
    def instruction_provider(ctx: ReadonlyContext) -> str:
        from ..prompts.builder import inject_template_variables_with_context_preloading
        context_type = ctx.state.get("validation_context", "research_plan")
        base_instruction = SENIOR_VALIDATOR_INSTRUCTIONS.get(context_type, SENIOR_VALIDATOR_INSTRUCTIONS["research_plan"])
        return inject_template_variables_with_context_preloading(base_instruction, ctx, "Senior_Validator")

    agent = LlmAgent(
        model=get_llm_model(config.VALIDATOR_MODEL),
        name=agent_name,
        instruction=instruction_provider,
        tools=tools,
        after_model_callback=ensure_end_of_output
    )
    _validator_agent_cache[agent_name] = agent
    return agent


def create_specialized_parallel_validator(validator_type: str, index: int, validation_context: str) -> BaseAgent:
    """Create a specialized validator for parallel validation based on context."""
    
    # Only use mock agent in actual dry_run mode with LLM skipping
    if config.EXECUTION_MODE == "dry_run" and config.DRY_RUN_SKIP_LLM:
        from ..tools.mock_llm_agent import create_mock_llm_agent
        return create_mock_llm_agent(name=f"{validator_type}_{index}")
    
    # Use the centralized toolset registry
    from ..tools.toolset_registry import toolset_registry
    desktop_commander_toolset = toolset_registry.get_desktop_commander_toolset()
    
    # Wrap in list if it's a real MCP toolset, mock tools are already a list
    if toolset_registry.is_using_real_mcp():
        tools = [desktop_commander_toolset]
    else:
        tools = desktop_commander_toolset
    
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
    
    # Use the provided validation_context to select the right configuration
    config_key = validation_context.split("_")[0] if validation_context else "research"
    
    validator_config = validator_configs.get(config_key, validator_configs["research_plan"])
    validator_info = list(validator_config.values())[index % len(validator_config)]
    
    instruction_template = f"""
        ### Persona ###
        You are a {validator_info['name']} for ULTRATHINK_QUANTITATIVEMarketAlpha parallel validation.
        Today's date is: {{current_date}}

        ### Context & State ###
        Artifact to validate: {{artifact_to_validate}}
        Validation context: {{validation_context}}
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
        1. Write your findings to the specified file
        2. After writing the file, end your response with "<end of output>"
        3. DO NOT put "<end of output>" inside the file content
        """

    def instruction_provider(ctx: ReadonlyContext) -> str:
        from ..prompts.builder import inject_template_variables_with_context_preloading
        agent_name = f"{validator_info['name']}_{index}"
        return inject_template_variables_with_context_preloading(instruction_template, ctx, agent_name)

    return LlmAgent(
        model=get_llm_model(config.VALIDATOR_MODEL),
        name=f"{validator_info['name']}_{index}",
        instruction=instruction_provider,
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
        
        # Always create new validators to avoid state leakage between loops
        validators = []
        
        # Create specialized validators based on context
        for i in range(config.PARALLEL_VALIDATION_SAMPLES):
            validator = create_specialized_parallel_validator(
                validator_type=self._get_validator_type(validation_context, i),
                index=i,
                validation_context=validation_context
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
        """Analyze validation results by parsing parallel validator output files."""
        import os
        import re
        from .. import config
        
        task_id = ctx.session.state.get('task_id', config.TASK_ID)
        outputs_dir = config.get_outputs_dir(task_id)
        validation_version = ctx.session.state.get('validation_version', 0)
        
        critical_issues = []
        validators_with_issues = []
        validation_context = ctx.session.state.get('validation_context', 'research_plan')
        
        # Get the list of validator types that were actually run for this context
        validator_types_to_check = [self._get_validator_type(validation_context, i) for i in range(config.PARALLEL_VALIDATION_SAMPLES)]
        
        for validator_type in set(validator_types_to_check): # Use set to avoid duplicates
            output_file = os.path.join(outputs_dir, f"parallel_validation_{validator_type}_v{validation_version}.md")
            
            if os.path.exists(output_file):
                try:
                    with open(output_file, 'r') as f:
                        content = f.read()
                    
                    # Check if critical issues were found
                    if "No critical" not in content and len(content.strip()) > 50:
                        # This validator found issues
                        validators_with_issues.append(validator_type)
                        
                        # Extract specific issues (looking for bullet points or numbered items)
                        issue_patterns = [
                            r'[-•*]\s*(.+)',  # Bullet points
                            r'\d+\.\s*(.+)',  # Numbered lists
                            r'Issue:\s*(.+)',  # Explicit issue markers
                            r'Problem:\s*(.+)',  # Problem markers
                        ]
                        
                        found_in_file = []
                        for pattern in issue_patterns:
                            matches = re.findall(pattern, content, re.MULTILINE)
                            for match in matches:
                                if len(match.strip()) > 10:  # Filter out very short matches
                                    found_in_file.append(f"[{validator_type}] {match.strip()}")
                        
                        if not found_in_file:
                            # If no specific patterns match, add the whole content as an issue
                            critical_issues.append(f"[{validator_type}] General feedback: {content.strip()}")
                        else:
                            critical_issues.extend(found_in_file)
                
                except Exception as e:
                    print(f"Error reading {output_file}: {e}")
        
        # Update session state based on findings
        if critical_issues:
            ctx.session.state['validation_status'] = 'critical_error'
            print(f"PARALLEL VALIDATION: Found critical issues from validators: {', '.join(set(validators_with_issues))}")
        else:
            ctx.session.state['validation_status'] = 'approved'
            print("PARALLEL VALIDATION: No critical issues found by any validator")
        
        return critical_issues
    
    def _find_latest_senior_critique(self, ctx: InvocationContext) -> str:
        """Find the latest senior critique file."""
        import os
        from .. import config
        
        task_id = ctx.session.state.get('task_id', config.TASK_ID)
        outputs_dir = config.get_outputs_dir(task_id)
        critiques_dir = os.path.join(outputs_dir, "planning", "critiques")
        
        if not os.path.exists(critiques_dir):
            return None
        
        # Find all senior critique files
        senior_critiques = []
        for filename in os.listdir(critiques_dir):
            if filename.startswith("senior_critique_v") and filename.endswith(".md"):
                senior_critiques.append(filename)
        
        if not senior_critiques:
            return None
        
        # Sort by version number to get latest
        senior_critiques.sort(key=lambda x: int(x.split('_v')[1].split('.')[0]))
        latest_critique = senior_critiques[-1]
        
        return os.path.join(critiques_dir, latest_critique)


def _find_latest_critique(ctx: InvocationContext, validator_role: str) -> Optional[str]:
    """Finds the latest critique file for a given validator role."""
    import os
    from .. import config
    
    task_id = ctx.session.state.get('task_id', config.TASK_ID)
    outputs_dir = config.get_outputs_dir(task_id)
    # This is a simplification; a more robust solution would check the current validation context
    critiques_dir = os.path.join(outputs_dir, "planning", "critiques")

    if not os.path.isdir(critiques_dir):
        return None

    critique_files = []
    for f in os.listdir(critiques_dir):
        if f.startswith(f"{validator_role}_critique_v") and f.endswith(".md"):
            critique_files.append(os.path.join(critiques_dir, f))

    if not critique_files:
        return None

    # Find the one with the highest version number from the filename
    def get_version(filepath):
        filename = os.path.basename(filepath)
        try:
            # Extracts version number like '2' from 'senior_critique_v2.md'
            return int(re.search(r'_v(\d+)\.md', filename).group(1))
        except (AttributeError, IndexError, ValueError):
            return -1

    latest_critique = max(critique_files, key=get_version)
    return latest_critique

async def _parse_status_from_critique(critique_path: str) -> Optional[str]:
    """Parses the validation status from a critique file."""
    if not critique_path or not os.path.exists(critique_path):
        return None
    
    try:
        with open(critique_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        status_match = re.search(r'\*\*FINAL VALIDATION STATUS:\s*(approved|rejected|critical_error)\*\*', content, re.IGNORECASE)
        
        if status_match:
            return status_match.group(1).lower()
    except Exception as e:
        print(f"Error parsing critique file {critique_path}: {e}")
    return None


# This is not an LLM agent. It's a simple control-flow agent.
class MetaValidatorCheckAgent(BaseAgent):
    """Checks the state for 'validation_status' and escalates based on the status."""
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        status = ctx.session.state.get("validation_status")

        # If status is not set (i.e., not a dry run), parse it from the senior validator's output file.
        if status is None or status == "pending":
            latest_senior_critique = _find_latest_critique(ctx, "senior")
            if latest_senior_critique:
                print(f"META VALIDATOR: Reading status from {os.path.basename(latest_senior_critique)}")
                parsed_status = await _parse_status_from_critique(latest_senior_critique)
                if parsed_status:
                    status = parsed_status
                    ctx.session.state["validation_status"] = status
                    print(f"META VALIDATOR: Parsed status '{status}' from critique.")
                else:
                    print("META VALIDATOR: Could not parse status from critique, assuming 'rejected' to continue loop.")
                    status = "rejected"
            else:
                # This can happen on the very first run before any critique is written.
                print("META VALIDATOR: No senior critique file found, assuming 'rejected' to continue loop.")
                status = "rejected"
        
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
            # Set the task to 'refine_plan' for the next iteration
            ctx.session.state["current_task"] = "refine_plan"
            # Increment the version for the refinement
            new_version = ctx.session.state.get("plan_version", 0) + 1
            ctx.session.state["plan_version"] = new_version
            ctx.session.state["validation_version"] = new_version
            # ** THE FIX: Clear the cache to get fresh validator instances for the next loop **
            clear_validator_cache()
        
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