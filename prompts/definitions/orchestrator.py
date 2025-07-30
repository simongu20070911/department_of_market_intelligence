"""
Orchestrator agent prompt construction.
"""

from ..builder import PromptBuilder
from ..components.personas import ORCHESTRATOR_PERSONA
from ..components.tasks import (
    GENERATE_IMPLEMENTATION_PLAN_TASK,
    GENERATE_RESULTS_EXTRACTION_PLAN_TASK
)


def build_orchestrator_prompt() -> str:
    """Build the Orchestrator prompt from components."""
    builder = PromptBuilder()
    
    # Add parallelization rules section
    parallelization_rules = """### PARALLELIZATION RULES YOU MUST FOLLOW ###
- Data fetching from different sources MUST be parallel
- Feature engineering for orthogonal features MUST be parallel  
- Model training with different algorithms/parameters MUST be parallel
- Only add dependencies for actual data flow, not "logical" ordering
- Prefer 10 parallel tasks over 3 sequential ones
- Each parallel stream should have clear convergence points"""
    
    parallel_structure_example = """### EXAMPLE PARALLEL STRUCTURE for quantitative research ###
```
# Parallel Stream 1: Market Data
market_data_fetch → market_data_validate → market_data_clean → market_features

# Parallel Stream 2: Alternative Data  
alt_data_fetch → alt_data_validate → alt_data_clean → alt_features

# Parallel Stream 3: Risk Data
risk_data_fetch → risk_data_validate → risk_data_clean → risk_features

# Convergence Point 1: Feature Matrix
[market_features, alt_features, risk_features] → feature_matrix_assembly

# Parallel Model Training
feature_matrix_assembly → [model_rf, model_xgb, model_nn, model_linear]

# Parallel Analysis  
[models] → [backtest_is, backtest_oos, risk_analysis, factor_attribution]
```"""
    
    return builder\
        .add_persona(ORCHESTRATOR_PERSONA)\
        .add_communication_protocol_with_path_validation()\
        .add_directory_structure_spec()\
        .add_context()\
        .add_tasks([
            GENERATE_IMPLEMENTATION_PLAN_TASK,
            GENERATE_RESULTS_EXTRACTION_PLAN_TASK
        ])\
        .add_section(parallelization_rules)\
        .add_section(parallel_structure_example)\
        .add_output_format()\
        .build()


# Export the built prompt
ORCHESTRATOR_INSTRUCTION = build_orchestrator_prompt()