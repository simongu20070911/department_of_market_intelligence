#!/usr/bin/env python3
"""Test script for context-aware validation system."""

import os
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.validation_context import ValidationContextManager
from utils.state_model import SessionState
import config


def create_test_artifacts():
    """Create test artifacts for each validation context."""
    test_dir = Path(config.OUTPUTS_DIR) / "validation_tests"
    test_dir.mkdir(exist_ok=True, parents=True)
    
    # Test research plan
    research_plan = """# Research Plan: Momentum Factor Analysis

## Hypothesis
Momentum factors exhibit stronger predictive power during high volatility regimes.

## Data Requirements
- Daily price data for S&P 500 constituents (2015-2025)
- VIX data for volatility regime classification
- Corporate actions data for adjustments

## Experiments to be Conducted
1. Calculate rolling momentum factors (1M, 3M, 6M, 12M)
2. Classify volatility regimes using VIX thresholds
3. Test momentum performance across regimes using t-tests
4. Apply Bonferroni correction for multiple testing

## Statistical Tests
- Paired t-tests for regime performance differences
- Augmented Dickey-Fuller test for stationarity
- Jarque-Bera test for normality assumptions
"""
    
    plan_path = test_dir / "research_plan_v1.md"
    plan_path.write_text(research_plan)
    
    # Test implementation manifest
    manifest = {
        "tasks": [
            {
                "task_id": "fetch_price_data",
                "description": "Fetch S&P 500 price data",
                "dependencies": [],
                "parallel_group": "data_fetch",
                "interface_contract": {
                    "output_schema": {
                        "columns": ["date", "symbol", "open", "high", "low", "close", "volume"],
                        "types": ["datetime", "str", "float", "float", "float", "float", "int"]
                    }
                }
            },
            {
                "task_id": "fetch_vix_data",
                "description": "Fetch VIX data",
                "dependencies": [],
                "parallel_group": "data_fetch",
                "interface_contract": {
                    "output_schema": {
                        "columns": ["date", "vix_close"],
                        "types": ["datetime", "float"]
                    }
                }
            }
        ]
    }
    
    manifest_path = test_dir / "implementation_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    
    # Test code implementation
    code = """import pandas as pd
import numpy as np
from typing import Dict, Any

def calculate_momentum(prices: pd.DataFrame, lookback: int = 252) -> pd.DataFrame:
    \"\"\"Calculate momentum factors for given lookback period.\"\"\"
    if prices.empty:
        raise ValueError("Empty price dataframe")
    
    # Calculate returns
    returns = prices.pct_change(lookback)
    
    # Handle missing data
    returns = returns.fillna(0)
    
    return returns

def classify_volatility_regimes(vix: pd.Series, thresholds: Dict[str, float]) -> pd.Series:
    \"\"\"Classify market regimes based on VIX levels.\"\"\"
    regimes = pd.Series(index=vix.index, dtype='str')
    
    regimes[vix < thresholds['low']] = 'low_vol'
    regimes[(vix >= thresholds['low']) & (vix < thresholds['high'])] = 'medium_vol'
    regimes[vix >= thresholds['high']] = 'high_vol'
    
    return regimes
"""
    
    code_path = test_dir / "momentum_calculation.py"
    code_path.write_text(code)
    
    # Test experiment journal
    journal = """# Experiment Execution Journal

## Execution started: 2025-01-28 10:00:00

### Parameters:
- Momentum lookbacks: [21, 63, 126, 252]
- VIX thresholds: {'low': 15, 'high': 25}
- Test period: 2020-01-01 to 2024-12-31

### Execution Log:
[10:00:15] Loading price data... SUCCESS (1,258,000 rows)
[10:01:30] Loading VIX data... SUCCESS (1,259 rows)
[10:02:00] Calculating momentum factors... SUCCESS
[10:05:45] Running statistical tests... SUCCESS

### Results:
- High vol regime momentum: 0.0145 (t-stat: 3.45, p-value: 0.0006)
- Low vol regime momentum: 0.0023 (t-stat: 0.89, p-value: 0.3741)
- Regime difference significant at 0.01 level
"""
    
    journal_path = test_dir / "experiment_journal.md"
    journal_path.write_text(journal)
    
    # Test results extraction
    extraction = """import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load experiment results
results = pd.read_csv('experiment_results.csv')

# Aggregate by regime
regime_summary = results.groupby('regime').agg({
    'returns': ['mean', 'std', 'sharpe'],
    't_stat': 'mean',
    'p_value': 'mean'
})

# Create final summary statistics
final_results = {
    'momentum_effectiveness': regime_summary.loc['high_vol', ('returns', 'mean')] / 
                             regime_summary.loc['low_vol', ('returns', 'mean')],
    'statistical_significance': (regime_summary['p_value'] < 0.05).sum() / len(regime_summary),
    'economic_significance': regime_summary[('returns', 'sharpe')].max()
}

# Generate visualizations
plt.figure(figsize=(12, 6))
regime_summary[('returns', 'mean')].plot(kind='bar')
plt.title('Momentum Returns by Volatility Regime')
plt.savefig('outputs/regime_performance.png')
"""
    
    extraction_path = test_dir / "extract_results.py"
    extraction_path.write_text(extraction)
    
    return {
        "research_plan": str(plan_path),
        "implementation_manifest": str(manifest_path),
        "code_implementation": str(code_path),
        "experiment_execution": str(journal_path),
        "results_extraction": str(extraction_path)
    }


def test_context_detection():
    """Test the validation context detection system."""
    print("\n" + "="*80)
    print("TESTING CONTEXT-AWARE VALIDATION SYSTEM")
    print("="*80)
    
    # Create test artifacts
    test_files = create_test_artifacts()
    
    # Test each context type
    for expected_context, file_path in test_files.items():
        print(f"\n📋 Testing: {expected_context}")
        print(f"   File: {file_path}")
        
        # Detect context
        detected_context, confidence = ValidationContextManager.detect_validation_context(file_path)
        
        # Check results
        success = detected_context == expected_context
        symbol = "✅" if success else "❌"
        
        print(f"   {symbol} Detected: {detected_context} (confidence: {confidence:.2%})")
        
        if not success:
            print(f"   ⚠️  MISMATCH: Expected '{expected_context}' but got '{detected_context}'")
    
    print("\n" + "-"*80)
    
    # Test unknown file
    print("\n📋 Testing unknown file type")
    unknown_path = Path(config.OUTPUTS_DIR) / "validation_tests" / "unknown.txt"
    unknown_path.write_text("This is just some random text file.")
    
    detected, confidence = ValidationContextManager.detect_validation_context(str(unknown_path))
    print(f"   File: {unknown_path}")
    print(f"   Detected: {detected} (confidence: {confidence:.2%})")
    
    # Test state preparation
    print("\n" + "-"*80)
    print("\n🔧 Testing state preparation")
    
    # Create test session state
    test_state = SessionState(
        task_id="test_validation",
        current_task="validate_plan",
        task_file_path=test_files["research_plan"],
        artifact_to_validate=test_files["research_plan"]
    )
    # Set validation version in the nested validation_info
    test_state.validation_info.validation_version = 1
    # Set current phase for context detection
    test_state.current_phase = "planning"
    
    # Convert to dict and prepare
    state_dict = test_state.to_checkpoint_dict()
    prepared_state = ValidationContextManager.prepare_validation_state(state_dict)
    
    print(f"   Original state keys: {list(state_dict.keys())}")
    print(f"   Added keys: {set(prepared_state.keys()) - set(state_dict.keys())}")
    print(f"   Validation context: {prepared_state.get('validation_context')}")
    
    # Test focus areas
    print("\n" + "-"*80)
    print("\n🎯 Testing focus area retrieval")
    
    for context_type in ["research_plan", "implementation_manifest", "code_implementation"]:
        print(f"\n   Context: {context_type}")
        focus_areas = ValidationContextManager.get_validator_focus_areas(context_type)
        
        print("   Junior focuses on:")
        for focus in focus_areas.get("junior", [])[:3]:
            print(f"     • {focus}")
        
        print("   Senior focuses on:")
        for focus in focus_areas.get("senior", [])[:3]:
            print(f"     • {focus}")
    
    print("\n" + "="*80)
    print("✅ Context-aware validation system test complete!")
    print("="*80 + "\n")


if __name__ == "__main__":
    test_context_detection()