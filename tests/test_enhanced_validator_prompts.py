#!/usr/bin/env python3
"""Test the enhanced validator prompts for different contexts."""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the prompt dictionaries directly to avoid import issues
JUNIOR_VALIDATOR_PROMPTS = {
    "research_plan": "Data availability edge cases, Statistical assumption failures, Market regime dependencies, Lookahead bias risks",
    "implementation_manifest": "Missing dependencies, Resource conflicts, Interface contracts, Error handling boundaries",
    "code_implementation": "Critical bugs, Data leakage risks, Performance bottlenecks, Integration failures",
    "experiment_execution": "Missing experiment steps, Parameter setting errors, Data loading issues, Result storage problems",
    "results_extraction": "Missing required outputs, Aggregation logic errors, Visualization problems, Calculation mistakes"
}

SENIOR_VALIDATOR_PROMPTS = {
    "research_plan": "Statistical power & sample size, Hypothesis clarity, Data hygiene protocols, Experimental design robustness",
    "implementation_manifest": "Parallelization efficiency, Surgical alignment points, Success criteria measurability, Task boundary definition",
    "code_implementation": "Success criteria compliance, Interface contract adherence, Statistical correctness, Integration readiness",
    "experiment_execution": "Experimental protocol adherence, Statistical test execution, Result completeness, Reproducibility documentation",
    "results_extraction": "Completeness vs requirements, Statistical summary accuracy, Result interpretation validity, Presentation clarity"
}

def get_validation_context(session_state):
    """Simple validation context detection for testing."""
    current_task = session_state.get('current_task', '')
    artifact_path = session_state.get('artifact_to_validate', '')
    
    if 'generate_initial_plan' in current_task or 'refine_plan' in current_task:
        return 'research_plan'
    elif 'implementation_manifest' in artifact_path or 'implementation_plan' in current_task:
        return 'implementation_manifest'
    elif 'extract_results' in artifact_path or 'results_extraction' in current_task:
        return 'results_extraction'
    elif 'experiment' in current_task or 'execution_log' in artifact_path:
        return 'experiment_execution'
    elif any(ext in artifact_path for ext in ['.py', '.ipynb', '_code.', '_implementation.']):
        return 'code_implementation'
    else:
        return 'research_plan'
from utils.state_model import SessionState
import config


def test_prompt_differentiation():
    """Test that validator prompts are properly differentiated by context."""
    print("\n" + "="*80)
    print("TESTING ENHANCED VALIDATOR PROMPT DIFFERENTIATION")
    print("="*80)
    
    contexts = [
        "research_plan",
        "implementation_manifest", 
        "code_implementation",
        "experiment_execution",
        "results_extraction"
    ]
    
    print("\n📋 Junior Validator Prompt Differentiation:")
    print("-" * 60)
    
    for context in contexts:
        prompt = JUNIOR_VALIDATOR_PROMPTS.get(context, "NOT FOUND")
        if prompt != "NOT FOUND":
            # Extract key focus areas from prompt
            lines = prompt.split('\n')
            focus_sections = [line.strip() for line in lines if line.strip().startswith('1.') or line.strip().startswith('2.')]
            
            print(f"\n🔍 {context.replace('_', ' ').title()}:")
            if focus_sections:
                for section in focus_sections[:2]:  # Show first 2 sections
                    print(f"   • {section}")
            else:
                # Look for other indicators
                critical_areas = [line.strip() for line in lines if "###" in line and "Critical" in line]
                if critical_areas:
                    print(f"   • {critical_areas[0].replace('###', '').strip()}")
        else:
            print(f"\n❌ {context}: NO PROMPT FOUND")
    
    print("\n📋 Senior Validator Prompt Differentiation:")
    print("-" * 60)
    
    for context in contexts:
        prompt = SENIOR_VALIDATOR_PROMPTS.get(context, "NOT FOUND")
        if prompt != "NOT FOUND":
            # Extract comprehensive review areas
            lines = prompt.split('\n')
            review_sections = [line.strip() for line in lines if line.strip().startswith('1.') or line.strip().startswith('2.')]
            
            print(f"\n🔍 {context.replace('_', ' ').title()}:")
            if review_sections:
                for section in review_sections[:2]:  # Show first 2 sections
                    print(f"   • {section}")
            else:
                # Look for comprehensive review indicators
                review_areas = [line.strip() for line in lines if "###" in line and ("Review" in line or "Analysis" in line)]
                if review_areas:
                    print(f"   • {review_areas[0].replace('###', '').strip()}")
        else:
            print(f"\n❌ {context}: NO PROMPT FOUND")


def test_context_specific_focus():
    """Test that each context has specific focus areas that differentiate it."""
    print("\n" + "="*80)  
    print("TESTING CONTEXT-SPECIFIC FOCUS AREAS")
    print("="*80)
    
    # Key terms that should appear in specific contexts
    expected_terms = {
        "research_plan": {
            "junior": ["data availability", "statistical assumption", "lookahead bias", "market regime"],
            "senior": ["statistical power", "hypothesis clarity", "data hygiene", "experimental design"]
        },
        "implementation_manifest": {
            "junior": ["dependencies", "resource conflicts", "interface contract", "error handling"],
            "senior": ["parallelization efficiency", "alignment points", "success criteria", "task boundaries"]
        },
        "code_implementation": {
            "junior": ["critical bugs", "data leakage", "performance bottlenecks", "integration"],
            "senior": ["success criteria compliance", "interface contract adherence", "statistical correctness"]
        },
        "experiment_execution": {
            "junior": ["missing steps", "parameter errors", "data loading", "result storage"],
            "senior": ["protocol adherence", "statistical test execution", "reproducibility"]
        },
        "results_extraction": {
            "junior": ["missing outputs", "aggregation logic", "visualization", "calculation"],
            "senior": ["completeness", "statistical summary", "interpretation validity", "presentation"]
        }
    }
    
    all_passed = True
    
    for context, expected in expected_terms.items():
        print(f"\n🔍 Testing {context.replace('_', ' ').title()}:")
        
        for role in ["junior", "senior"]:
            prompt_dict = JUNIOR_VALIDATOR_PROMPTS if role == "junior" else SENIOR_VALIDATOR_PROMPTS
            prompt = prompt_dict.get(context, "")
            
            if not prompt:
                print(f"   ❌ {role.title()}: No prompt found")
                all_passed = False
                continue
            
            prompt_lower = prompt.lower()
            found_terms = []
            missing_terms = []
            
            for term in expected[role]:
                if any(keyword in prompt_lower for keyword in term.lower().split()):
                    found_terms.append(term)
                else:
                    missing_terms.append(term)
            
            coverage = len(found_terms) / len(expected[role]) * 100
            symbol = "✅" if coverage >= 75 else "⚠️" if coverage >= 50 else "❌"
            
            print(f"   {symbol} {role.title()}: {coverage:.0f}% coverage")
            if missing_terms and coverage < 75:
                print(f"      Missing: {', '.join(missing_terms[:3])}")
            
            if coverage < 50:
                all_passed = False
    
    print(f"\n{'✅' if all_passed else '❌'} Overall focus differentiation: {'PASSED' if all_passed else 'NEEDS IMPROVEMENT'}")


def test_validation_context_detection():
    """Test the get_validation_context function with different session states."""
    print("\n" + "="*80)
    print("TESTING VALIDATION CONTEXT DETECTION FROM SESSION STATE")
    print("="*80)
    
    test_cases = [
        {
            "name": "Research Plan Generation",
            "state": {"current_task": "generate_initial_plan", "artifact_to_validate": "research_plan_v1.md"},
            "expected": "research_plan"
        },
        {
            "name": "Plan Refinement", 
            "state": {"current_task": "refine_plan", "artifact_to_validate": "research_plan_v2.md"},
            "expected": "research_plan"
        },
        {
            "name": "Implementation Planning",
            "state": {"current_task": "implementation_plan", "artifact_to_validate": "implementation_manifest.json"},
            "expected": "implementation_manifest"
        },
        {
            "name": "Code Validation",
            "state": {"current_task": "validate_code", "artifact_to_validate": "momentum_calc.py"},
            "expected": "code_implementation"
        },
        {
            "name": "Experiment Journal",
            "state": {"current_task": "experiment_validation", "artifact_to_validate": "execution_log.md"},
            "expected": "experiment_execution"
        },
        {
            "name": "Results Extraction",
            "state": {"current_task": "results_extraction", "artifact_to_validate": "extract_results.py"},
            "expected": "results_extraction"
        }
    ]
    
    all_correct = True
    
    for test_case in test_cases:
        detected = get_validation_context(test_case["state"])
        correct = detected == test_case["expected"]
        symbol = "✅" if correct else "❌"
        
        print(f"\n{symbol} {test_case['name']}")
        print(f"   State: {test_case['state']}")
        print(f"   Expected: {test_case['expected']}")
        print(f"   Detected: {detected}")
        
        if not correct:
            all_correct = False
    
    print(f"\n{'✅' if all_correct else '❌'} Context detection: {'ALL CORRECT' if all_correct else 'SOME ERRORS'}")


def test_prompt_completeness():
    """Test that all prompts have required sections."""
    print("\n" + "="*80)
    print("TESTING PROMPT COMPLETENESS")
    print("="*80)
    
    required_sections = {
        "junior": ["### Persona ###", "### Context & State ###", "### Task ###", "### Output Format ###"],
        "senior": ["### Persona ###", "### Context & State ###", "### Task ###", "### Output Format ###"]
    }
    
    contexts = ["research_plan", "implementation_manifest", "code_implementation", "experiment_execution", "results_extraction"]
    
    all_complete = True
    
    for role in ["junior", "senior"]:
        print(f"\n📋 {role.title()} Validator Completeness:")
        prompt_dict = JUNIOR_VALIDATOR_PROMPTS if role == "junior" else SENIOR_VALIDATOR_PROMPTS
        
        for context in contexts:
            prompt = prompt_dict.get(context, "")
            missing_sections = []
            
            for section in required_sections[role]:
                if section not in prompt:
                    missing_sections.append(section)
            
            if missing_sections:
                print(f"   ❌ {context}: Missing {missing_sections}")
                all_complete = False
            else:
                print(f"   ✅ {context}: Complete")
    
    print(f"\n{'✅' if all_complete else '❌'} Prompt completeness: {'ALL COMPLETE' if all_complete else 'SOME INCOMPLETE'}")


if __name__ == "__main__":
    test_prompt_differentiation()
    test_context_specific_focus()
    test_validation_context_detection()
    test_prompt_completeness()
    
    print("\n" + "="*80)
    print("✅ ENHANCED VALIDATOR PROMPTS TEST COMPLETE!")
    print("="*80 + "\n")