"""
Prompt builder utilities for composing prompts from components.
The builder only orchestrates - all content lives in component files.
"""

from typing import Dict, List, Optional, Set
from .. import config
from ..utils.state_adapter import get_domi_state


class PromptBuilder:
    """Builds prompts from components with validation."""
    
    def __init__(self):
        self.sections: List[str] = []
        self.required_vars: Set[str] = set()
    
    def add_section(self, template: str, required_vars: Optional[List[str]] = None) -> 'PromptBuilder':
        """Add a section to the prompt."""
        self.sections.append(template)
        if required_vars:
            self.required_vars.update(required_vars)
        return self
    
    def add_persona(self, persona: str) -> 'PromptBuilder':
        """Add persona section."""
        return self.add_section(persona)
    
    def add_communication_protocol_with_path_validation(self) -> 'PromptBuilder':
        """Add enhanced communication protocol with path validation."""
        from .base import COMMUNICATION_PROTOCOL_WITH_PATH_VALIDATION, PATH_VALIDATION_RULES
        return (self.add_section(COMMUNICATION_PROTOCOL_WITH_PATH_VALIDATION, ['agent_name', 'outputs_dir', 'current_task'])
                   .add_section(PATH_VALIDATION_RULES, ['outputs_dir']))
    
    def add_context(self) -> 'PromptBuilder':
        """Add standard context section."""
        from .base import BASE_CONTEXT
        return self.add_section(BASE_CONTEXT, ['current_task', 'current_date', 'current_year'])
    
    def add_time_context(self) -> 'PromptBuilder':
        """Add time context section."""
        from .base import TIME_CONTEXT
        return self.add_section(TIME_CONTEXT, ['current_date', 'current_year'])
    
    def add_directory_structure_spec(self) -> 'PromptBuilder':
        """Add comprehensive directory structure specification."""
        from .base import DIRECTORY_STRUCTURE_SPEC
        return self.add_section(DIRECTORY_STRUCTURE_SPEC, ['outputs_dir', 'validation_version'])
    
    def add_tasks(self, tasks: List[str]) -> 'PromptBuilder':
        """Add multiple task sections."""
        for task in tasks:
            self.add_section(task)
        return self
    
    def add_output_format(self) -> 'PromptBuilder':
        """Add standard output format."""
        from .base import OUTPUT_FORMAT
        return self.add_section(OUTPUT_FORMAT)
    
    def add_validator_output_format(self) -> 'PromptBuilder':
        """Add validator-specific output format with status marker."""
        from .base import VALIDATOR_OUTPUT_FORMAT
        return self.add_section(VALIDATOR_OUTPUT_FORMAT)
    
    def build(self) -> str:
        """Build the final prompt."""
        return "\n\n".join(self.sections)
    
    def validate_vars(self, provided_vars: Dict[str, any]) -> bool:
        """Validate that all required variables are provided."""
        return self.required_vars.issubset(provided_vars.keys())
    
    def get_required_vars(self) -> Set[str]:
        """Get the set of required variables."""
        return self.required_vars.copy()


def inject_template_variables(template: str, ctx, agent_name: str) -> str:
    """Inject all template variables needed by the enhanced communication protocol."""
    from .. import config
    from datetime import datetime
    
    domi_state = get_domi_state(ctx)

    task_id = domi_state.task_id or config.TASK_ID
    outputs_dir = config.get_outputs_dir(task_id)
    
    if "validator" in agent_name.lower():
        validation_context = domi_state.validation.validation_context or "research_plan"
        current_task = f"validate_{validation_context}"
    else:
        current_task = domi_state.current_task_description or "TASK_NOT_SET_IN_STATE"
    current_date = datetime.now().strftime("%Y-%m-%d")
    current_year = str(datetime.now().year)
    validation_version = str(domi_state.validation.validation_version or 0)
    
    plan_version = str(domi_state.metadata.get("plan_version") or 0)
    next_version = str(int(plan_version) + 1)
    
    task_file_path = f"{config.TASKS_DIR}/{task_id}.md"
    
    artifact_to_validate = domi_state.validation.artifact_to_validate or "ARTIFACT_NOT_SET_IN_STATE"
    
    validation_context = domi_state.validation.validation_context or "research_plan"
    
    result = template
    replacements = {
        "{agent_name}": agent_name,
        "{outputs_dir}": outputs_dir,
        "{current_task}": current_task,
        "{current_date}": current_date,
        "{current_year}": current_year,
        "{task_id}": task_id,
        "{validation_version}": validation_version,
        "{plan_version}": plan_version,
        "{plan_version?}": plan_version,
        "{next_version}": next_version,
        "{task_file_path}": task_file_path,
        "{artifact_to_validate}": artifact_to_validate,
        "{validation_context}": validation_context,
    }
    
    for placeholder, value in replacements.items():
        result = result.replace(placeholder, str(value) if value is not None else "")
    
    return result


def inject_preloaded_context_variables(template: str, ctx, agent_name: str) -> str:
    """
    Enhanced template injection that includes pre-loaded context files.
    This eliminates the need for agents to manually discover and read files.
    """
    result = inject_template_variables(template, ctx, agent_name)
    
    domi_state = get_domi_state(ctx)
    
    if not config.ENABLE_CONTEXT_PRELOADING:
        return result
    
    preloaded_context = domi_state.metadata.get('preloaded_context', {})
    
    if not preloaded_context:
        from ..utils.agent_context_preloader import preload_context_for_agent
        
        try:
            preloaded_context = preload_context_for_agent(agent_name, domi_state.dict())
            domi_state.metadata['preloaded_context'] = preloaded_context
        except Exception as e:
            print(f"⚠️  Failed to pre-load context for {agent_name}: {e}")
            return result
    
    for template_var, content in preloaded_context.items():
        placeholder = f"{{{template_var}}}"
        if placeholder in result and content:
            formatted_content = f"```\n{content}\n```" if content else "(No content available)"
            result = result.replace(placeholder, formatted_content)
    
    return result


def inject_template_variables_with_context_preloading(template: str, ctx, agent_name: str) -> str:
    """
    Complete template injection with context pre-loading support.
    Use this as the main injection function for agents that support context pre-loading.
    """
    return inject_preloaded_context_variables(template, ctx, agent_name)


class ContextAwarePromptBuilder(PromptBuilder):
    """Extended builder with context-aware features."""
    
    def add_validation_context(self, validation_type: str) -> 'ContextAwarePromptBuilder':
        """Add validation-specific instructions based on type."""
        from .components.validation import VALIDATION_CONTEXT_MAP
        
        if validation_type in VALIDATION_CONTEXT_MAP:
            self.add_section(VALIDATION_CONTEXT_MAP[validation_type])
        
        return self