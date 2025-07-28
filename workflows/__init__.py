# /department_of_market_intelligence/workflows/__init__.py
from .root_workflow import get_root_workflow
from .research_planning_workflow import get_research_planning_workflow
# from .orchestrator_workflow import get_orchestrator_workflow  # Not implemented yet
# from .coder_workflow import get_coder_workflow  # Not implemented yet  
# from .experiment_workflow import get_experiment_workflow  # Not implemented yet

# Context-aware workflows
from .research_planning_workflow_context_aware import (
    get_context_aware_research_planning_workflow,
    get_context_aware_orchestrator_workflow,
    get_context_aware_code_validation_workflow,
    get_context_aware_experiment_validation_workflow,
    get_context_aware_results_validation_workflow
)

__all__ = [
    'get_root_workflow',
    'get_research_planning_workflow',
    # 'get_orchestrator_workflow',
    # 'get_coder_workflow',
    # 'get_experiment_workflow',
    # Context-aware workflows
    'get_context_aware_research_planning_workflow',
    'get_context_aware_orchestrator_workflow',
    'get_context_aware_code_validation_workflow',
    'get_context_aware_experiment_validation_workflow',
    'get_context_aware_results_validation_workflow',
]