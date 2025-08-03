# /department_of_market_intelligence/workflows/__init__.py
# Active workflows (no context-aware versions)
from .coder_workflow import get_coder_workflow, create_validation_loop
from .experiment_workflow import get_experiment_workflow

# Context-aware workflows (these are the primary ones used)
from .root_workflow_context_aware import get_context_aware_root_workflow
from .research_planning_workflow_context_aware import (
    get_context_aware_research_planning_workflow,
    get_context_aware_orchestrator_workflow,
    get_context_aware_code_validation_workflow,
    get_context_aware_experiment_validation_workflow,
    get_context_aware_results_validation_workflow
)
from .implementation_workflow_context_aware import ImplementationWorkflowAgentContextAware

__all__ = [
    # Active workflows
    'get_coder_workflow',
    'get_experiment_workflow', 
    'create_validation_loop',
    # Context-aware workflows (primary)
    'get_context_aware_root_workflow',
    'get_context_aware_research_planning_workflow',
    'get_context_aware_orchestrator_workflow',
    'get_context_aware_code_validation_workflow',
    'get_context_aware_experiment_validation_workflow',
    'get_context_aware_results_validation_workflow',
    'ImplementationWorkflowAgentContextAware',
]