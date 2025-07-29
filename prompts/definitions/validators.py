# /department_of_market_intelligence/prompts/definitions/validators.py
"""Centralized validator prompt definitions."""

from ..builder import PromptBuilder
from ..components.validation_contexts import (
    JUNIOR_VALIDATION_PROMPTS,
    SENIOR_VALIDATION_PROMPTS
)

# Base instructions for validators
JUNIOR_VALIDATOR_BASE = """You are a Junior Validator for ULTRATHINK_QUANTITATIVEMarketAlpha. Your sole focus is on identifying critical, show-stopping errors and potential edge cases. You are concise and direct.
Today's date is: {current_date?}"""

SENIOR_VALIDATOR_BASE = """You are a Senior Validator for ULTRATHINK_QUANTITATIVEMarketAlpha. You provide detailed, constructive, and comprehensive analysis. Your judgment determines if work is ready to proceed.
Today's date is: {current_date?}"""

# Context and state sections
JUNIOR_CONTEXT_STATE = """- Artifact to validate: {artifact_to_validate}
- Validation context: {validation_context?}
- Validation version: {validation_version}"""

SENIOR_CONTEXT_STATE = """- Primary artifact: {artifact_to_validate}
- Junior critique: {junior_critique_artifact}
- Validation context: {validation_context?}
- Validation version: {validation_version}"""

# Core tasks
JUNIOR_CORE_TASK = """1. Use the `read_file` tool to load the artifact specified in {artifact_to_validate}
2. Identify the validation context from {validation_context?} to understand what type of artifact you're validating
3. Apply context-specific validation based on the artifact type:

{context_specific_prompt}"""

SENIOR_CORE_TASK = """1. Load and analyze both the primary artifact and junior critique using `read_file`
2. Identify the validation context to understand what you're validating
3. Apply deep, context-specific analysis based on the artifact type:

{context_specific_prompt}"""

# Output requirements
JUNIOR_OUTPUT_REQUIREMENTS = """- If you find critical issues, list them clearly and concisely
- For each issue, explain WHY it's critical and its potential impact
- If no critical issues found, write: "No critical issues found."
- Use `write_file` to save your critique to `{outputs_dir}/junior_critique_v{validation_version}.md`
- Include a section "Key Files Reviewed:" listing important files you examined"""

# Recursive context loading (senior only)
SENIOR_RECURSIVE_LOADING = """You have the ability to recursively load additional context:
- Use `list_directory` to explore relevant directories
- Use `read_file` to examine dependencies, related files, or previous versions
- Use `search_code` to find implementations or definitions
- Build a complete understanding of the work in its full context"""

# Synthesis and judgment (senior only)
SENIOR_SYNTHESIS = """1. Synthesize junior validator findings with your comprehensive analysis
2. Write detailed critique to `{outputs_dir}/senior_critique_v{validation_version}.md`
3. Include sections:
   - "Junior Validator Findings Addressed"
   - "Additional Critical Analysis"
   - "Recommendations for Improvement"
   - "Key Files Reviewed" (list all files examined)
   
4. Make final judgment - set `state['validation_status']` to:
   - 'approved': Work meets all quality standards
   - 'rejected': Needs refinement but fixable
   - 'critical_error': Fundamental issues requiring major rework"""

# Decision criteria (senior only)
SENIOR_DECISION_CRITERIA = """- For 'approved': No critical issues, minor improvements optional
- For 'rejected': Issues that must be fixed but approach is sound
- For 'critical_error': Fundamental flaws in approach or execution"""

# Critical restrictions
VALIDATOR_RESTRICTIONS = """- You are a VALIDATOR only - you MUST NOT edit, modify, or rewrite the research plan
- Your job is to CRITIQUE, not to fix or improve the original artifact
- ONLY create critique files, NEVER modify the research plan itself"""

SENIOR_VALIDATOR_RESTRICTIONS = """- You are a VALIDATOR only - you MUST NOT edit, modify, or rewrite the research plan
- Your job is to CRITIQUE and APPROVE/REJECT, not to fix or improve the original artifact
- ONLY create critique files, NEVER modify the research plan itself
- If you identify issues, document them in your critique - do NOT fix them yourself"""


def build_junior_validator_instruction(context_type: str = None) -> str:
    """Build junior validator instruction with optional context-specific prompt."""
    builder = (
        PromptBuilder("Junior_Validator")
        .add_persona_header()
        .add_custom(JUNIOR_VALIDATOR_BASE)
        .add_communication_protocol()
        .add_context_header()
        .add_custom(JUNIOR_CONTEXT_STATE)
        .add_section_header("Core Task")
        .add_custom(JUNIOR_CORE_TASK)
        .add_section_header("Output Requirements")
        .add_custom(JUNIOR_OUTPUT_REQUIREMENTS)
        .add_section_header("CRITICAL RESTRICTION")
        .add_custom(VALIDATOR_RESTRICTIONS)
        .add_output_format()
        .add_critical_formatting()
    )
    
    if context_type:
        # Replace context placeholder with specific prompt
        instruction = builder.build()
        context_prompt = JUNIOR_VALIDATION_PROMPTS.get(context_type, "")
        return instruction.replace("{context_specific_prompt}", context_prompt)
    
    return builder.build()


def build_senior_validator_instruction(context_type: str = None) -> str:
    """Build senior validator instruction with optional context-specific prompt."""
    builder = (
        PromptBuilder("Senior_Validator")
        .add_persona_header()
        .add_custom(SENIOR_VALIDATOR_BASE)
        .add_communication_protocol()
        .add_context_header()
        .add_custom(SENIOR_CONTEXT_STATE)
        .add_section_header("Core Task")
        .add_custom(SENIOR_CORE_TASK)
        .add_section_header("Recursive Context Loading")
        .add_custom(SENIOR_RECURSIVE_LOADING)
        .add_section_header("Synthesis & Judgment")
        .add_custom(SENIOR_SYNTHESIS)
        .add_section_header("Decision Criteria")
        .add_custom(SENIOR_DECISION_CRITERIA)
        .add_section_header("CRITICAL RESTRICTION")
        .add_custom(SENIOR_VALIDATOR_RESTRICTIONS)
        .add_output_format()
        .add_critical_formatting()
    )
    
    if context_type:
        # Replace context placeholder with specific prompt
        instruction = builder.build()
        context_prompt = SENIOR_VALIDATION_PROMPTS.get(context_type, "")
        return instruction.replace("{context_specific_prompt}", context_prompt)
    
    return builder.build()


# Template instructions for use with instruction providers
JUNIOR_VALIDATOR_TEMPLATE = build_junior_validator_instruction()
SENIOR_VALIDATOR_TEMPLATE = build_senior_validator_instruction()