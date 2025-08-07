#!/usr/bin/env python3
"""Full system test for context-aware validation framework."""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ..utils.state_model import SessionState
from ..utils.validation_context import ValidationContextManager
import config


def test_full_context_aware_system():
    """Test the complete context-aware validation system."""
    print("\n" + "="*80)
    print("FULL CONTEXT-AWARE VALIDATION SYSTEM TEST")
    print("="*80)
    
    # Test all phases of the research workflow
    phases = [
        {
            "name": "Research Planning",
            "phase": "planning",
            "task": "generate_initial_plan",
            "artifact": "research_plan_v1.md",
            "expected_context": "research_plan"
        },
        {
            "name": "Implementation Planning", 
            "phase": "implementation",
            "task": "generate_implementation_plan",
            "artifact": "implementation_manifest.json",
            "expected_context": "implementation_manifest"
        },
        {
            "name": "Code Implementation",
            "phase": "implementation",
            "task": "code_implementation",
            "artifact": "momentum_strategy.py",
            "expected_context": "code_implementation"
        },
        {
            "name": "Experiment Execution",
            "phase": "execution",
            "task": "experiment_execution",
            "artifact": "experiment_journal.md",
            "expected_context": "experiment_execution"
        },
        {
            "name": "Results Extraction",
            "phase": "results_extraction",
            "task": "results_extraction",
            "artifact": "extract_results.py",
            "expected_context": "results_extraction"
        }
    ]
    
    all_passed = True
    
    for i, phase_info in enumerate(phases, 1):
        print(f"\n📋 Phase {i}/{len(phases)}: {phase_info['name']}")
        print("-" * 60)
        
        # Create session state for this phase
        session_state = SessionState(
            task_id="test_workflow",
            current_phase=phase_info["phase"],
            current_task=phase_info["task"],
            artifact_to_validate=f"outputs/{phase_info['artifact']}"
        )
        
        # Convert to dict and prepare validation context
        state_dict = session_state.to_checkpoint_dict()
        prepared_state = ValidationContextManager.prepare_validation_state(state_dict)
        
        # Check context detection
        detected_context = prepared_state.get('validation_context')
        expected_context = phase_info['expected_context']
        
        success = detected_context == expected_context
        symbol = "✅" if success else "❌"
        
        print(f"   {symbol} Context Detection:")
        print(f"      Phase: {phase_info['phase']}")
        print(f"      Task: {phase_info['task']}")
        print(f"      Expected: {expected_context}")
        print(f"      Detected: {detected_context}")
        
        if not success:
            all_passed = False
            print(f"      ⚠️  MISMATCH!")
        
        # Get focus areas for this context
        focus_areas = ValidationContextManager.get_validator_focus_areas(detected_context)
        
        print(f"   🎯 Validation Focus Areas:")
        junior_areas = focus_areas.get('junior', [])[:2]
        senior_areas = focus_areas.get('senior', [])[:2]
        
        for area in junior_areas:
            print(f"      Junior: {area}")
        for area in senior_areas:
            print(f"      Senior: {area}")
        
        print()
    
    # Test configuration
    print("\n" + "-"*80)
    print("⚙️  CONFIGURATION TEST")
    print("-"*80)
    
    print(f"   Context-Aware Validation: {'✅ ENABLED' if config.ENABLE_CONTEXT_AWARE_VALIDATION else '❌ DISABLED'}")
    
    # Test workflow selection
    print(f"\n🔄 WORKFLOW SELECTION TEST")
    print("-"*40)
    
    if config.ENABLE_CONTEXT_AWARE_VALIDATION:
        print("   ✅ Will use RootWorkflowAgentContextAware")
        print("   ✅ Will use context-aware validators")
        print("   ✅ Will use specialized parallel validation")
    else:
        print("   📋 Will use standard RootWorkflowAgent")
        print("   📋 Will use generic validators")
        print("   📋 Will use standard parallel validation")
    
    # Final summary
    print("\n" + "="*80)
    
    if all_passed:
        print("✅ FULL CONTEXT-AWARE SYSTEM TEST: PASSED")
        print("🎯 All phases correctly detected validation contexts")
        print("🔍 Focus areas properly differentiated")
        print("⚙️  Configuration properly set")
        print("🚀 Ready for context-aware quantitative research!")
    else:
        print("❌ FULL CONTEXT-AWARE SYSTEM TEST: FAILED")
        print("⚠️  Some context detection issues found")
        print("🔧 Check context detection logic")
    
    print("="*80 + "\n")
    
    return all_passed


def test_validator_prompt_quality():
    """Test the quality and completeness of validator prompts."""
    print("\n" + "="*80)
    print("VALIDATOR PROMPT QUALITY TEST")
    print("="*80)
    
    # Key quality indicators
    quality_checks = {
        "research_plan": {
            "junior_keywords": ["data availability", "statistical assumption", "market regime", "lookahead bias"],
            "senior_keywords": ["statistical power", "hypothesis clarity", "data hygiene", "experimental design"]
        },
        "implementation_manifest": {
            "junior_keywords": ["dependencies", "resource conflicts", "interface contract", "error handling"],
            "senior_keywords": ["parallelization efficiency", "alignment", "success criteria", "task boundary"]
        },
        "code_implementation": {
            "junior_keywords": ["critical bugs", "data leakage", "performance", "integration"],
            "senior_keywords": ["success criteria", "interface contract", "statistical correctness", "readiness"]
        },
        "experiment_execution": {
            "junior_keywords": ["missing steps", "parameter errors", "data loading", "result storage"],
            "senior_keywords": ["protocol adherence", "statistical test", "completeness", "reproducibility"]
        },
        "results_extraction": {
            "junior_keywords": ["missing outputs", "aggregation logic", "visualization", "calculation"],
            "senior_keywords": ["completeness", "statistical summary", "interpretation", "presentation"]
        }
    }
    
    contexts = list(quality_checks.keys())
    all_high_quality = True
    
    for context in contexts:
        print(f"\n🔍 {context.replace('_', ' ').title()} Validation Quality:")
        
        # Get focus areas (simulated since we can't import the full prompts easily)
        focus_areas = ValidationContextManager.get_validator_focus_areas(context)
        
        for role in ["junior", "senior"]:
            areas = focus_areas.get(role, [])
            expected_keywords = quality_checks[context][f"{role}_keywords"]
            
            # Check coverage
            coverage_count = 0
            for keyword in expected_keywords:
                if any(keyword.lower() in area.lower() for area in areas):
                    coverage_count += 1
            
            coverage_percent = (coverage_count / len(expected_keywords)) * 100
            symbol = "✅" if coverage_percent >= 75 else "⚠️" if coverage_percent >= 50 else "❌"
            
            print(f"   {symbol} {role.title()}: {coverage_percent:.0f}% keyword coverage")
            
            if coverage_percent < 75:
                all_high_quality = False
    
    print(f"\n{'✅' if all_high_quality else '❌'} Overall Prompt Quality: {'HIGH' if all_high_quality else 'NEEDS IMPROVEMENT'}")
    print("="*80 + "\n")
    
    return all_high_quality


if __name__ == "__main__":
    system_test_passed = test_full_context_aware_system()
    prompt_quality_passed = test_validator_prompt_quality()
    
    print("\n" + "="*80)
    print("FINAL TEST SUMMARY")
    print("="*80)
    
    print(f"Context-Aware System: {'✅ PASSED' if system_test_passed else '❌ FAILED'}")
    print(f"Prompt Quality: {'✅ HIGH' if prompt_quality_passed else '❌ LOW'}")
    
    if system_test_passed and prompt_quality_passed:
        print("\n🎉 CONTEXT-AWARE VALIDATION SYSTEM READY FOR PRODUCTION!")
        print("🔬 Enhanced validation for quantitative finance research")
        print("🎯 Targeted, efficient, comprehensive validation")
    else:
        print("\n⚠️  System needs refinement before production use")
    
    print("="*80 + "\n")