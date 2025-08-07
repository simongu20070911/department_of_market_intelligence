# /department_of_market_intelligence/prompts/components/parallel_validator_configs.py
"""
Centralized configurations for parallel validators.
"""

from .contexts import JUNIOR_VALIDATION_PROMPTS

# A comprehensive validation prompt to be used as a default
comprehensive_validation = JUNIOR_VALIDATION_PROMPTS.get("research_plan", "")

PARALLEL_VALIDATOR_CONFIGS = {
    "research_plan": {
        "validator_0": {
            "name": "ParallelValidator_0",
            "focus": comprehensive_validation,
        },
        "validator_1": {
            "name": "ParallelValidator_1",
            "focus": comprehensive_validation,
        },
        "validator_2": {
            "name": "ParallelValidator_2",
            "focus": comprehensive_validation,
        },
        "validator_3": {
            "name": "ParallelValidator_3",
            "focus": comprehensive_validation,
        }
    },
    "implementation_manifest": {
        "validator_0": {
            "name": "ParallelValidator_0",
            "focus": JUNIOR_VALIDATION_PROMPTS.get("implementation_manifest", comprehensive_validation),
        },
        "validator_1": {
            "name": "ParallelValidator_1",
            "focus": JUNIOR_VALIDATION_PROMPTS.get("implementation_manifest", comprehensive_validation),
        },
        "validator_2": {
            "name": "ParallelValidator_2",
            "focus": JUNIOR_VALIDATION_PROMPTS.get("implementation_manifest", comprehensive_validation),
        },
        "validator_3": {
            "name": "ParallelValidator_3",
            "focus": JUNIOR_VALIDATION_PROMPTS.get("implementation_manifest", comprehensive_validation),
        }
    }
}