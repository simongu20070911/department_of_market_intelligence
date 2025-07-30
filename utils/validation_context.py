# /department_of_market_intelligence/utils/validation_context.py
"""Validation context detection and management for context-aware validators."""

import os
import re
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
import os

# Get outputs directory from environment or use default
OUTPUTS_DIR = os.environ.get('OUTPUTS_DIR', 'outputs')


class ValidationContextManager:
    """Manages validation context detection and prompt injection."""
    
    # Patterns to detect artifact types from filenames and content
    ARTIFACT_PATTERNS = {
        "research_plan": {
            "filename_patterns": [
                r"research_plan.*\.md",
                r"plan_v\d+\.md",
                r"chief_researcher_plan.*"
            ],
            "content_patterns": [
                r"hypothesis",
                r"experiments to be conducted",
                r"statistical tests",
                r"data sourcing"
            ]
        },
        "implementation_manifest": {
            "filename_patterns": [
                r"implementation_manifest\.json",
                r"orchestrator_plan.*",
                r"task_manifest.*"
            ],
            "content_patterns": [
                r"task_id",
                r"dependencies", 
                r"parallel_group",
                r"interface_contract"
            ]
        },
        "code_implementation": {
            "filename_patterns": [
                r".*\.py$",
                r"coder_\d+_.*",
                r"implementation_.*\.py"
            ],
            "content_patterns": [
                r"import pandas",
                r"def ",
                r"class ",
                r"return "
            ]
        },
        "experiment_execution": {
            "filename_patterns": [
                r"experiment_journal.*",
                r"execution_log.*",
                r"experiment_results.*"
            ],
            "content_patterns": [
                r"execution started",
                r"parameters:",
                r"results:",
                r"experiment:"
            ]
        },
        "results_extraction": {
            "filename_patterns": [
                r"extract_results\.py",
                r"results_extraction.*",
                r"final_analysis.*"
            ],
            "content_patterns": [
                r"aggregate",
                r"final_results",
                r"summary_statistics",
                r"visualization"
            ]
        }
    }
    
    @classmethod
    def detect_validation_context(cls, artifact_path: str) -> Tuple[str, float]:
        """
        Detect the validation context from artifact path and content.
        
        Returns:
            Tuple of (context_type, confidence_score)
        """
        if not artifact_path or not os.path.exists(artifact_path):
            return ("unknown", 0.0)
        
        # Get filename
        filename = os.path.basename(artifact_path)
        
        # Try to read file content (limit to first 1000 lines for performance)
        try:
            with open(artifact_path, 'r', encoding='utf-8') as f:
                content = '\n'.join(f.readlines()[:1000])
        except Exception:
            content = ""
        
        # Score each context type
        scores = {}
        for context_type, patterns in cls.ARTIFACT_PATTERNS.items():
            score = 0.0
            
            # Check filename patterns
            for pattern in patterns["filename_patterns"]:
                if re.search(pattern, filename, re.IGNORECASE):
                    score += 0.5
                    break
            
            # Check content patterns
            matches = 0
            for pattern in patterns["content_patterns"]:
                if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
                    matches += 1
            
            if patterns["content_patterns"]:
                score += (matches / len(patterns["content_patterns"])) * 0.5
            
            scores[context_type] = score
        
        # Get the best match
        best_context = max(scores.items(), key=lambda x: x[1])
        
        # If confidence is too low, return unknown
        if best_context[1] < 0.3:
            return ("unknown", best_context[1])
        
        return best_context
    
    @classmethod
    def inject_context_prompts(cls, base_instruction: str, context_type: str, role: str) -> str:
        """
        Inject context-specific prompts into the base instruction.
        
        Args:
            base_instruction: The base validator instruction template
            context_type: The detected validation context
            role: 'junior' or 'senior'
        
        Returns:
            Modified instruction with context-specific prompts
        """
        # Import here to avoid circular dependency
        from ..agents.validators import get_validation_context_prompt
        
        context_prompt = get_validation_context_prompt(context_type, role)
        
        # Replace the placeholder with actual context-specific prompt
        return base_instruction.replace("{context_specific_prompt}", context_prompt)
    
    @classmethod
    def prepare_validation_state(cls, session_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare the session state with validation context information.
        
        Args:
            session_state: The current session state
            
        Returns:
            Modified session state with validation context
        """
        # We can determine context from the current task and phase
        current_task = session_state.get('current_task', '')
        current_phase = session_state.get('current_phase', '')
        artifact_path = session_state.get('artifact_to_validate', '')
        
        # Direct context determination based on workflow phase and task
        # Order matters - check most specific first
        if 'implementation_plan' in current_task or 'generate_implementation_plan' in current_task:
            context_type = 'implementation_manifest'
        elif 'results' in current_task or 'extraction' in current_task:
            context_type = 'results_extraction'
        elif current_phase == 'planning' or 'plan' in current_task:
            context_type = 'research_plan'
        elif current_phase == 'implementation' and 'code' in current_task:
            context_type = 'code_implementation'
        elif current_phase == 'execution' or 'experiment' in current_task:
            context_type = 'experiment_execution'
        else:
            # Fallback to filename detection if needed
            context_type, _ = cls.detect_validation_context(artifact_path)
        
        session_state['validation_context'] = context_type
        print(f"🎯 Validation Context: {context_type} (from {current_phase}/{current_task})")
        
        return session_state
    
    @classmethod
    def get_validator_focus_areas(cls, context_type: str) -> Dict[str, list]:
        """
        Get the focus areas for validators based on context type.
        
        Returns:
            Dict with junior and senior focus area lists
        """
        focus_areas = {
            "research_plan": {
                "junior": [
                    "Data availability edge cases",
                    "Statistical assumption failures", 
                    "Market regime dependencies",
                    "Lookahead bias risks",
                    "Computational edge cases"
                ],
                "senior": [
                    "Statistical rigor & power analysis",
                    "Hypothesis clarity & testability",
                    "Data hygiene protocol completeness",
                    "Missing interesting relationships",
                    "Experimental design robustness",
                    "Result interpretation framework"
                ]
            },
            "implementation_manifest": {
                "junior": [
                    "Missing task dependencies",
                    "Resource allocation conflicts",
                    "Undefined interface contracts", 
                    "Error propagation gaps",
                    "Timing and timeout issues"
                ],
                "senior": [
                    "Parallelization efficiency",
                    "Surgical alignment clarity",
                    "Success criteria measurability",
                    "Task boundary definitions",
                    "Experiment logging structure",
                    "Research plan alignment"
                ]
            },
            "code_implementation": {
                "junior": [
                    "Critical bugs and errors",
                    "Data leakage risks",
                    "Performance bottlenecks",
                    "Edge case handling",
                    "Integration failures"
                ],
                "senior": [
                    "Success criteria compliance",
                    "Interface contract adherence",
                    "Statistical correctness",
                    "Data transformation validity",
                    "Integration readiness",
                    "Performance optimization"
                ]
            },
            "experiment_execution": {
                "junior": [
                    "Missing experiment steps",
                    "Parameter setting errors",
                    "Data loading issues",
                    "Result storage problems",
                    "Environment issues"
                ],
                "senior": [
                    "Protocol adherence",
                    "Statistical test execution",
                    "Result completeness",
                    "Reproducibility documentation",
                    "Quality control checks",
                    "Execution journal quality"
                ]
            },
            "results_extraction": {
                "junior": [
                    "Missing required outputs",
                    "Aggregation logic errors",
                    "Visualization problems",
                    "Calculation mistakes",
                    "Export format issues"
                ],
                "senior": [
                    "Research question coverage",
                    "Statistical summary accuracy",
                    "Interpretation validity",
                    "Presentation quality",
                    "Data integrity verification",
                    "Actionable insights extraction"
                ]
            }
        }
        
        return focus_areas.get(context_type, {
            "junior": ["General critical issues"],
            "senior": ["Comprehensive quality analysis"]
        })
    
    @classmethod
    def format_validation_report(cls, context_type: str, issues: list, role: str) -> str:
        """
        Format validation report based on context type.
        
        Args:
            context_type: The validation context
            issues: List of identified issues
            role: 'junior' or 'senior'
            
        Returns:
            Formatted validation report
        """
        report = f"# {role.title()} Validation Report\n\n"
        report += f"**Validation Context**: {context_type.replace('_', ' ').title()}\n"
        report += f"**Issues Found**: {len(issues)}\n\n"
        
        if not issues:
            report += "✅ No critical issues found.\n"
            return report
        
        # Get focus areas for context
        focus_areas = cls.get_validator_focus_areas(context_type)
        validator_focuses = focus_areas.get(role, [])
        
        # Categorize issues by focus area
        categorized = {area: [] for area in validator_focuses}
        uncategorized = []
        
        for issue in issues:
            categorized_flag = False
            for area in validator_focuses:
                # Simple keyword matching - could be enhanced
                if any(keyword.lower() in issue.lower() 
                      for keyword in area.lower().split()):
                    categorized[area].append(issue)
                    categorized_flag = True
                    break
            if not categorized_flag:
                uncategorized.append(issue)
        
        # Write categorized issues
        for area, area_issues in categorized.items():
            if area_issues:
                report += f"## {area}\n\n"
                for issue in area_issues:
                    report += f"- {issue}\n"
                report += "\n"
        
        # Write uncategorized issues
        if uncategorized:
            report += "## Other Issues\n\n"
            for issue in uncategorized:
                report += f"- {issue}\n"
            report += "\n"
        
        return report