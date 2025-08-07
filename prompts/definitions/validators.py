# /department_of_market_intelligence/prompts/definitions/validators.py
"""Centralized validator prompt definitions."""

from ..builder import PromptBuilder
from ..components.personas import JUNIOR_VALIDATOR_PERSONA, SENIOR_VALIDATOR_PERSONA
from ..components.contexts import (
    JUNIOR_VALIDATOR_CONTEXT,
    SENIOR_VALIDATOR_CONTEXT,
    JUNIOR_VALIDATION_PROMPTS,
    SENIOR_VALIDATION_PROMPTS
)
from ..components.tasks import (
    JUNIOR_VALIDATOR_CORE_TASK,
    SENIOR_VALIDATOR_CORE_TASK,
    JUNIOR_VALIDATOR_OUTPUT_REQUIREMENTS,
    SENIOR_VALIDATOR_COMPREHENSIVE_ANALYSIS,
    SENIOR_VALIDATOR_SYNTHESIS,
    SENIOR_VALIDATOR_DECISION_CRITERIA,
    VALIDATOR_RESTRICTIONS,
    SENIOR_VALIDATOR_RESTRICTIONS
)
from ..components.parallel_validator import PARALLEL_VALIDATOR_INSTRUCTION


def build_junior_validator_instruction(context_type: str = None, task_description: str = "") -> str:
    """Build junior validator instruction with optional context-specific prompt."""
    builder = (
        PromptBuilder()
        .add_section("### Persona ###")
        .add_section(JUNIOR_VALIDATOR_PERSONA)
        .add_communication_protocol()
        .add_directory_structure_spec()
        .add_section("### Context & State ###")
        .add_section(JUNIOR_VALIDATOR_CONTEXT)
        .add_section("### Core Task ###")
        .add_section(JUNIOR_VALIDATOR_CORE_TASK)
        .add_section("### Output Requirements ###")
        .add_section(JUNIOR_VALIDATOR_OUTPUT_REQUIREMENTS)
        .add_section("### CRITICAL RESTRICTION ###")
        .add_section(VALIDATOR_RESTRICTIONS)
        .add_validator_output_format()
    )
    
    instruction = builder.build()
    if context_type:
        # Replace context placeholder with specific prompt
        context_prompt = JUNIOR_VALIDATION_PROMPTS.get(context_type, "")
        instruction = instruction.replace("{context_specific_prompt}", context_prompt)

    if task_description:
        instruction = instruction.replace("{task_description}", task_description)
    
    return instruction


def build_senior_validator_instruction(context_type: str = None, task_description: str = "") -> str:
    """Build senior validator instruction with optional context-specific prompt."""
    builder = (
        PromptBuilder()
        .add_section("### Persona ###")
        .add_section(SENIOR_VALIDATOR_PERSONA)
        .add_communication_protocol()
        .add_directory_structure_spec()
        .add_section("### Context & State ###")
        .add_section(SENIOR_VALIDATOR_CONTEXT)
        .add_section("### Core Task ###")
        .add_section(SENIOR_VALIDATOR_CORE_TASK)
        .add_section("### Comprehensive Analysis ###")
        .add_section(SENIOR_VALIDATOR_COMPREHENSIVE_ANALYSIS)
        .add_section("### Synthesis & Judgment ###")
        .add_section(SENIOR_VALIDATOR_SYNTHESIS)
        .add_section("### Decision Criteria ###")
        .add_section(SENIOR_VALIDATOR_DECISION_CRITERIA)
        .add_section("### CRITICAL RESTRICTION ###")
        .add_section(SENIOR_VALIDATOR_RESTRICTIONS)
        .add_validator_output_format()
    )
    
    instruction = builder.build()
    if context_type:
        # Replace context placeholder with specific prompt
        context_prompt = SENIOR_VALIDATION_PROMPTS.get(context_type, "")
        instruction = instruction.replace("{context_specific_prompt}", context_prompt)

    if task_description:
        instruction = instruction.replace("{task_description}", task_description)
    
    return instruction


# Template instructions for use with instruction providers
JUNIOR_VALIDATOR_TEMPLATE = build_junior_validator_instruction()
SENIOR_VALIDATOR_TEMPLATE = build_senior_validator_instruction()

# Complete static instructions for all validation contexts
JUNIOR_VALIDATOR_RESEARCH_PLAN = build_junior_validator_instruction("research_plan")
SENIOR_VALIDATOR_RESEARCH_PLAN = build_senior_validator_instruction("research_plan")

JUNIOR_VALIDATOR_IMPLEMENTATION_MANIFEST = build_junior_validator_instruction("implementation_manifest")
SENIOR_VALIDATOR_IMPLEMENTATION_MANIFEST = build_senior_validator_instruction("implementation_manifest")

JUNIOR_VALIDATOR_CODE_IMPLEMENTATION = build_junior_validator_instruction("code_implementation")
SENIOR_VALIDATOR_CODE_IMPLEMENTATION = build_senior_validator_instruction("code_implementation")

JUNIOR_VALIDATOR_EXPERIMENT_EXECUTION = build_junior_validator_instruction("experiment_execution")
SENIOR_VALIDATOR_EXPERIMENT_EXECUTION = build_senior_validator_instruction("experiment_execution")

JUNIOR_VALIDATOR_RESULTS_EXTRACTION = build_junior_validator_instruction("results_extraction")
SENIOR_VALIDATOR_RESULTS_EXTRACTION = build_senior_validator_instruction("results_extraction")

# Context mapping for easy selection
JUNIOR_VALIDATOR_INSTRUCTIONS = {
    "research_plan": JUNIOR_VALIDATOR_RESEARCH_PLAN,
    "implementation_manifest": JUNIOR_VALIDATOR_IMPLEMENTATION_MANIFEST,
    "code_implementation": JUNIOR_VALIDATOR_CODE_IMPLEMENTATION,
    "experiment_execution": JUNIOR_VALIDATOR_EXPERIMENT_EXECUTION,
    "results_extraction": JUNIOR_VALIDATOR_RESULTS_EXTRACTION,
}

SENIOR_VALIDATOR_INSTRUCTIONS = {
    "research_plan": SENIOR_VALIDATOR_RESEARCH_PLAN,
    "implementation_manifest": SENIOR_VALIDATOR_IMPLEMENTATION_MANIFEST,
    "code_implementation": SENIOR_VALIDATOR_CODE_IMPLEMENTATION,
    "experiment_execution": SENIOR_VALIDATOR_EXPERIMENT_EXECUTION,
    "results_extraction": SENIOR_VALIDATOR_RESULTS_EXTRACTION,
}