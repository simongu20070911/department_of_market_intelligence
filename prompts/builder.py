"""
Prompt builder utilities for composing prompts from components.
The builder only orchestrates - all content lives in component files.
"""

from typing import Dict, List, Optional, Set


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
    
    def add_communication_protocol(self) -> 'PromptBuilder':
        """Add standard communication protocol."""
        from .base import COMMUNICATION_PROTOCOL
        return self.add_section(COMMUNICATION_PROTOCOL, ['agent_name', 'outputs_dir', 'current_task'])
    
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
    
    def add_file_path_context(self) -> 'PromptBuilder':
        """Add file path context section."""
        from .base import FILE_PATH_CONTEXT
        return self.add_section(FILE_PATH_CONTEXT, ['task_id', 'outputs_dir', 'task_file_path'])
    
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
    
    # Ensure ctx.state is a dictionary to prevent attribute errors
    session_state = ctx.state if isinstance(ctx.state, dict) else {}

    # Get basic variables from context and config, ensuring no None values
    task_id = session_state.get("task_id") or config.TASK_ID
    outputs_dir = config.get_outputs_dir(task_id)
    current_task = session_state.get("current_task") or "research_planning"
    current_date = datetime.now().strftime("%Y-%m-%d")
    current_year = str(datetime.now().year)
    validation_version = str(session_state.get("validation_version") or 0)
    
    # Get task file path
    task_file_path = f"{config.TASKS_DIR}/{task_id}.md"
    
    # Replace all template variables
    result = template
    replacements = {
        "{agent_name}": agent_name,
        "{outputs_dir}": outputs_dir,
        "{current_task}": current_task,
        "{current_date}": current_date,
        "{current_year}": current_year,
        "{task_id}": task_id,
        "{validation_version}": validation_version,
        "{task_file_path}": task_file_path,
    }
    
    for placeholder, value in replacements.items():
        # Ensure all values are strings before replacement to avoid TypeError
        result = result.replace(placeholder, str(value) if value is not None else "")
    
    return result


class ContextAwarePromptBuilder(PromptBuilder):
    """Extended builder with context-aware features."""
    
    def add_validation_context(self, validation_type: str) -> 'ContextAwarePromptBuilder':
        """Add validation-specific instructions based on type."""
        from .components.validation import VALIDATION_CONTEXT_MAP
        
        if validation_type in VALIDATION_CONTEXT_MAP:
            self.add_section(VALIDATION_CONTEXT_MAP[validation_type])
        
        return self