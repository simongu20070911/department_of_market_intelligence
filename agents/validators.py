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
from ..utils.state_adapter import get_domi_state
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
from ..utils.logger import get_logger

logger = get_logger(__name__)


def _create_validator_agent(agent_name: str, instruction_map: Dict[str, str], default_instruction: str) -> LlmAgent:
    """Generic factory for creating context-aware validator agents."""
    from ..tools.toolset_registry import toolset_registry
    from ..tools.json_validator import json_validator_tool

    desktop_commander_toolset = toolset_registry.get_desktop_commander_toolset()
    tools = [desktop_commander_toolset, json_validator_tool]

    def instruction_provider(ctx: ReadonlyContext) -> str:
        from ..prompts.builder import inject_template_variables_with_context_preloading
        domi_state = get_domi_state(ctx)
        context_type = domi_state.validation.validation_context
        instruction = instruction_map.get(context_type, default_instruction)
        return inject_template_variables_with_context_preloading(instruction, ctx, agent_name)

    return LlmAgent(
        model=get_llm_model(config.AGENT_MODELS["VALIDATOR"]),
        name=agent_name,
        instruction=instruction_provider,
        tools=tools,
        after_model_callback=ensure_end_of_output
    )

def get_junior_validator_agent():
    """Create a context-aware junior validator."""
    return _create_validator_agent(
        "Junior_Validator",
        JUNIOR_VALIDATOR_INSTRUCTIONS,
        JUNIOR_VALIDATOR_INSTRUCTIONS["research_plan"]
    )

def get_senior_validator_agent():
    """Create a context-aware senior validator."""
    return _create_validator_agent(
        "Senior_Validator",
        SENIOR_VALIDATOR_INSTRUCTIONS,
        SENIOR_VALIDATOR_INSTRUCTIONS["research_plan"]
    )


def get_meta_validator_check_agent():
    """Create a meta validator check agent."""
    return _create_validator_agent(
        "Meta_Validator_Check",
        SENIOR_VALIDATOR_INSTRUCTIONS,
        SENIOR_VALIDATOR_INSTRUCTIONS["research_plan"]
    )


def create_specialized_parallel_validator(validator_type: str, index: int, validation_context: str) -> BaseAgent:
    """Create a specialized validator for parallel validation based on context."""
    
    # Use the centralized toolset registry
    from ..tools.toolset_registry import toolset_registry
    desktop_commander_toolset = toolset_registry.get_desktop_commander_toolset()
    
    tools = [desktop_commander_toolset]
    
    # Import the centralized validation prompts that Junior and Senior use
    from ..prompts.components.parallel_validator_configs import PARALLEL_VALIDATOR_CONFIGS
    
    # Use the provided validation_context to select the right configuration
    config_key = validation_context.split("_")[0] if validation_context else "research"
    
    validator_config = PARALLEL_VALIDATOR_CONFIGS.get(config_key, PARALLEL_VALIDATOR_CONFIGS["research_plan"])
    validator_info = list(validator_config.values())[index % len(validator_config)]
    
    from ..prompts.definitions.parallel_validator import PARALLEL_VALIDATOR_INSTRUCTION
    instruction_template = PARALLEL_VALIDATOR_INSTRUCTION.format(focus=validator_info['focus'])

    def instruction_provider(ctx: ReadonlyContext) -> str:
        from ..prompts.builder import inject_template_variables_with_context_preloading
        # The agent name for the template is the generic one, not the indexed one
        agent_name = validator_info['name']
        # We inject the index separately for the output file path
        template = instruction_template.replace("{index}", str(index))
        return inject_template_variables_with_context_preloading(template, ctx, agent_name)

    return LlmAgent(
        model=get_llm_model(config.AGENT_MODELS["VALIDATOR"]),
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
        domi_state = get_domi_state(ctx)
        validation_context = domi_state.validation.validation_context
        
        validators = []
        
        parallel_phase_map = {
            "research_plan": WorkflowPhase.RESEARCH_PARALLEL_VALIDATION,
            "implementation_manifest": WorkflowPhase.ORCHESTRATION_VALIDATION,
            "code_implementation": WorkflowPhase.CODING_VALIDATION,
            "experiment_execution": WorkflowPhase.EXPERIMENT_VALIDATION,
            "results_extraction": WorkflowPhase.RESULTS_VALIDATION
        }
        
        parallel_phase = parallel_phase_map.get(validation_context, WorkflowPhase.RESEARCH_PARALLEL_VALIDATION)
        _, parallel_samples = enhanced_phase_manager.get_parallel_config(parallel_phase)
        for i in range(parallel_samples):
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
        
        logger.info(f"[ParallelFinalValidationAgent]: Running {parallel_samples} specialized validators for {validation_context}.")
        
        async for event in self._parallel_validators.run_async(ctx):
            yield event
        
        critical_issues = self._analyze_validation_results(ctx)
        
        if critical_issues:
            logger.warning(f"[ParallelFinalValidationAgent]: {len(critical_issues)} critical issues found.")
            domi_state.validation.validation_status = 'critical_error'
            domi_state.validation.consolidated_validation_issues = critical_issues
        else:
            logger.info("[ParallelFinalValidationAgent]: All validators passed.")
            domi_state.validation.validation_status = 'approved'
        
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
        
        domi_state = get_domi_state(ctx)
        task_id = domi_state.task_id
        outputs_dir = config.get_outputs_dir(task_id)
        validation_version = domi_state.validation.validation_version
        
        critical_issues = []
        validators_with_issues = []
        validation_context = domi_state.validation.validation_context
        
        parallel_phase_map = {
            "research_plan": WorkflowPhase.RESEARCH_PARALLEL_VALIDATION,
            "implementation_manifest": WorkflowPhase.ORCHESTRATION_VALIDATION,
            "code_implementation": WorkflowPhase.CODING_VALIDATION,
            "experiment_execution": WorkflowPhase.EXPERIMENT_VALIDATION,
            "results_extraction": WorkflowPhase.RESULTS_VALIDATION
        }
        
        parallel_phase = parallel_phase_map.get(validation_context, WorkflowPhase.RESEARCH_PARALLEL_VALIDATION)
        _, parallel_samples = enhanced_phase_manager.get_parallel_config(parallel_phase)
        validator_types_to_check = [self._get_validator_type(validation_context, i) for i in range(parallel_samples)]
        
        for validator_type in set(validator_types_to_check):
            output_file = os.path.join(outputs_dir, f"parallel_validation_{validator_type}_v{validation_version}.md")
            
            if os.path.exists(output_file):
                try:
                    with open(output_file, 'r') as f:
                        content = f.read()
                    
                    if "No critical" not in content and len(content.strip()) > 50:
                        validators_with_issues.append(validator_type)
                        
                        issue_patterns = [
                            r'[-•*]\s*(.+)',
                            r'\d+\.\s*(.+)',
                            r'Issue:\s*(.+)',
                            r'Problem:\s*(.+)',
                        ]
                        
                        found_in_file = []
                        for pattern in issue_patterns:
                            matches = re.findall(pattern, content, re.MULTILINE)
                            for match in matches:
                                if len(match.strip()) > 10:
                                    found_in_file.append(f"[{validator_type}] {match.strip()}")
                        
                        if not found_in_file:
                            critical_issues.append(f"[{validator_type}] General feedback: {content.strip()}")
                        else:
                            critical_issues.extend(found_in_file)
                
                except Exception as e:
                    logger.error(f"[ParallelFinalValidationAgent]: Error reading {output_file}: {e}")
        
        if critical_issues:
            domi_state.validation.validation_status = 'critical_error'
            logger.warning(f"[ParallelFinalValidationAgent]: Found critical issues from validators: {', '.join(set(validators_with_issues))}")
        else:
            domi_state.validation.validation_status = 'approved'
            logger.info("[ParallelFinalValidationAgent]: No critical issues found by any validator.")
        
        return critical_issues


# Export the context-aware validator functions
def get_context_aware_validators():
    """Get all context-aware validators."""
    return {
        'junior': get_junior_validator_agent,
        'senior': get_senior_validator_agent,
        'parallel': ParallelFinalValidationAgent,
        'meta_validator': get_meta_validator_check_agent
    }