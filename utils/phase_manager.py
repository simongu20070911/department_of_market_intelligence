"""
Enhanced Phase Management for ULTRATHINK_QUANTITATIVE MarketAlpha
Agentic Research Framework with granular phases and explicit agent roles.

This module provides:
- Granular phase definitions matching the iterative loops
- Explicit agent-to-phase mapping
- Validation objectives and criteria
- State machine for complex workflow transitions
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
import json
import os
from datetime import datetime, timezone


class WorkflowPhase(Enum):
    """
    Granular workflow phases for the agentic research framework.
    Each phase corresponds to a specific agent's responsibility and iterative loop.
    """
    # Chief Researcher's iterative planning loop
    RESEARCH_PLANNING = "research_planning"
    RESEARCH_VALIDATION = "research_validation"  # Junior/Senior validation loop
    RESEARCH_REFINEMENT = "research_refinement"  # Chief refines based on feedback
    RESEARCH_PARALLEL_VALIDATION = "research_parallel_validation"  # X samples validation
    
    # Orchestrator's implementation planning loop
    ORCHESTRATION_PLANNING = "orchestration_planning"
    ORCHESTRATION_VALIDATION = "orchestration_validation"
    ORCHESTRATION_REFINEMENT = "orchestration_refinement"
    
    # Parallel Coders' implementation loop
    CODING_ASSIGNMENT = "coding_assignment"  # Tasks distributed to coders
    CODING_IMPLEMENTATION = "coding_implementation"  # Parallel execution
    CODING_VALIDATION = "coding_validation"  # Code review and validation
    CODING_INTEGRATION = "coding_integration"  # Surgical alignment verification
    
    # Experiment Executor's loop
    EXPERIMENT_SETUP = "experiment_setup"
    EXPERIMENT_EXECUTION = "experiment_execution"
    EXPERIMENT_VALIDATION = "experiment_validation"
    EXPERIMENT_JOURNAL = "experiment_journal"  # Meticulous logging
    
    # Results extraction (Orchestrator-led)
    RESULTS_PLANNING = "results_planning"
    RESULTS_EXTRACTION = "results_extraction"
    RESULTS_VALIDATION = "results_validation"
    
    # Chief Researcher's final synthesis
    FINAL_ANALYSIS = "final_analysis"
    FINAL_REPORT = "final_report"
    
    # Error and recovery states
    ERROR = "error"
    RECOVERY = "recovery"
    
    @classmethod
    def from_string(cls, phase_str: str) -> Optional['WorkflowPhase']:
        """Convert string to phase enum, handling legacy values."""
        # Direct mapping
        for phase in cls:
            if phase.value == phase_str:
                return phase
        
        # Legacy mappings
        legacy_map = {
            "planning": cls.RESEARCH_PLANNING,
            "implementation": cls.ORCHESTRATION_PLANNING,
            "execution": cls.EXPERIMENT_EXECUTION,
            "final_report": cls.FINAL_REPORT,
            "implementation_planning": cls.ORCHESTRATION_PLANNING,
            "implementation_coding": cls.CODING_IMPLEMENTATION,
        }
        return legacy_map.get(phase_str.lower() if phase_str else None)


@dataclass
class ValidationCriteria:
    """Specific validation criteria for each phase."""
    statistical_rigor: bool = False
    data_hygiene: bool = False
    novel_insights: bool = False
    parallelization_efficiency: bool = False
    surgical_alignment: bool = False
    success_criteria_clarity: bool = False
    code_correctness: bool = False
    execution_completeness: bool = False
    result_significance: bool = False
    
    def to_dict(self) -> Dict[str, bool]:
        return {
            'statistical_rigor': self.statistical_rigor,
            'data_hygiene': self.data_hygiene,
            'novel_insights': self.novel_insights,
            'parallelization_efficiency': self.parallelization_efficiency,
            'surgical_alignment': self.surgical_alignment,
            'success_criteria_clarity': self.success_criteria_clarity,
            'code_correctness': self.code_correctness,
            'execution_completeness': self.execution_completeness,
            'result_significance': self.result_significance,
        }


@dataclass
class PhaseConfig:
    """Enhanced configuration for a workflow phase."""
    phase: WorkflowPhase
    primary_agent: str
    supporting_agents: List[str]
    valid_tasks: List[str]
    input_artifacts: List[str]
    output_artifacts: List[str]
    next_phases: List[WorkflowPhase]
    rollback_phases: List[WorkflowPhase]  # Where to go on failure
    validation_criteria: ValidationCriteria
    max_iterations: int  # Maximum iterations for this phase
    parallel_samples: int  # For parallel validation phases
    description: str


class EnhancedPhaseManager:
    """Enhanced phase management for the agentic research framework."""
    
    PHASE_CONFIGS = {
        # ========== RESEARCH PLANNING PHASES ==========
        WorkflowPhase.RESEARCH_PLANNING: PhaseConfig(
            phase=WorkflowPhase.RESEARCH_PLANNING,
            primary_agent="Chief_Researcher",
            supporting_agents=[],
            valid_tasks=[
                "load_research_task",
                "generate_initial_research_plan",
                "define_statistical_tests",
                "identify_novel_inquiries",
                "specify_data_requirements"
            ],
            input_artifacts=["task.md"],
            output_artifacts=["research_plan_v*.md", "statistical_design.json"],
            next_phases=[WorkflowPhase.RESEARCH_VALIDATION],
            rollback_phases=[],
            validation_criteria=ValidationCriteria(
                statistical_rigor=True,
                data_hygiene=True,
                novel_insights=True
            ),
            max_iterations=1,  # Initial generation
            parallel_samples=0,
            description="Chief Researcher creates comprehensive research plan with statistical rigor"
        ),
        
        WorkflowPhase.RESEARCH_VALIDATION: PhaseConfig(
            phase=WorkflowPhase.RESEARCH_VALIDATION,
            primary_agent="Junior_Validator",
            supporting_agents=["Senior_Validator"],
            valid_tasks=[
                "critique_edge_cases",
                "validate_statistical_approach",
                "check_data_hygiene",
                "synthesize_validation_feedback"
            ],
            input_artifacts=["research_plan_v*.md"],
            output_artifacts=["junior_critique_v*.md", "senior_critique_v*.md", "validation_synthesis.json"],
            next_phases=[WorkflowPhase.RESEARCH_REFINEMENT, WorkflowPhase.RESEARCH_PARALLEL_VALIDATION],
            rollback_phases=[WorkflowPhase.RESEARCH_PLANNING],
            validation_criteria=ValidationCriteria(
                statistical_rigor=True,
                data_hygiene=True
            ),
            max_iterations=3,  # Max validation rounds
            parallel_samples=0,
            description="Junior and Senior validators critique the research plan"
        ),
        
        WorkflowPhase.RESEARCH_REFINEMENT: PhaseConfig(
            phase=WorkflowPhase.RESEARCH_REFINEMENT,
            primary_agent="Chief_Researcher",
            supporting_agents=[],
            valid_tasks=[
                "review_validation_feedback",
                "refine_research_plan",
                "update_statistical_design",
                "enhance_novel_inquiries"
            ],
            input_artifacts=["validation_synthesis.json", "research_plan_v*.md"],
            output_artifacts=["research_plan_v*.md", "refinement_log.json"],
            next_phases=[WorkflowPhase.RESEARCH_VALIDATION],
            rollback_phases=[WorkflowPhase.RESEARCH_PLANNING],
            validation_criteria=ValidationCriteria(
                statistical_rigor=True,
                novel_insights=True
            ),
            max_iterations=5,  # Max refinement iterations
            parallel_samples=0,
            description="Chief Researcher refines plan based on validation feedback"
        ),
        
        WorkflowPhase.RESEARCH_PARALLEL_VALIDATION: PhaseConfig(
            phase=WorkflowPhase.RESEARCH_PARALLEL_VALIDATION,
            primary_agent="Meta_Validator",
            supporting_agents=["Junior_Validator", "Senior_Validator"],
            valid_tasks=[
                "parallel_validation_sample",
                "consolidate_parallel_feedback",
                "final_approval_check"
            ],
            input_artifacts=["research_plan_v*.md"],
            output_artifacts=["parallel_validation_*.md", "final_approval.json"],
            next_phases=[WorkflowPhase.ORCHESTRATION_PLANNING],
            rollback_phases=[WorkflowPhase.RESEARCH_REFINEMENT],
            validation_criteria=ValidationCriteria(
                statistical_rigor=True,
                data_hygiene=True,
                novel_insights=True
            ),
            max_iterations=1,
            parallel_samples=4,  # Configurable X samples
            description="Parallel validation to spot potential issues before proceeding"
        ),
        
        # ========== ORCHESTRATION PHASES ==========
        WorkflowPhase.ORCHESTRATION_PLANNING: PhaseConfig(
            phase=WorkflowPhase.ORCHESTRATION_PLANNING,
            primary_agent="Orchestrator",
            supporting_agents=[],
            valid_tasks=[
                "decompose_research_plan",
                "define_parallel_subtasks",
                "specify_integration_points",
                "create_success_criteria",
                "design_experiment_logging"
            ],
            input_artifacts=["research_plan_v*.md", "final_approval.json"],
            output_artifacts=["orchestration_plan.json", "subtask_definitions/*.md", "integration_spec.json"],
            next_phases=[WorkflowPhase.ORCHESTRATION_VALIDATION],
            rollback_phases=[WorkflowPhase.RESEARCH_PARALLEL_VALIDATION],
            validation_criteria=ValidationCriteria(
                parallelization_efficiency=True,
                surgical_alignment=True,
                success_criteria_clarity=True
            ),
            max_iterations=1,
            parallel_samples=0,
            description="Orchestrator creates parallelizable implementation plan"
        ),
        
        WorkflowPhase.ORCHESTRATION_VALIDATION: PhaseConfig(
            phase=WorkflowPhase.ORCHESTRATION_VALIDATION,
            primary_agent="Junior_Validator",
            supporting_agents=["Senior_Validator"],
            valid_tasks=[
                "validate_task_decomposition",
                "check_surgical_alignment",
                "verify_success_criteria",
                "assess_parallelization"
            ],
            input_artifacts=["orchestration_plan.json"],
            output_artifacts=["orchestration_critique_v*.md", "alignment_validation.json"],
            next_phases=[WorkflowPhase.ORCHESTRATION_REFINEMENT, WorkflowPhase.CODING_ASSIGNMENT],
            rollback_phases=[WorkflowPhase.ORCHESTRATION_PLANNING],
            validation_criteria=ValidationCriteria(
                parallelization_efficiency=True,
                surgical_alignment=True
            ),
            max_iterations=3,
            parallel_samples=0,
            description="Validate orchestration plan for efficiency and alignment"
        ),
        
        WorkflowPhase.ORCHESTRATION_REFINEMENT: PhaseConfig(
            phase=WorkflowPhase.ORCHESTRATION_REFINEMENT,
            primary_agent="Orchestrator",
            supporting_agents=[],
            valid_tasks=[
                "review_orchestration_feedback",
                "refine_task_decomposition",
                "improve_integration_spec",
                "clarify_success_criteria"
            ],
            input_artifacts=["orchestration_critique_v*.md", "orchestration_plan.json"],
            output_artifacts=["orchestration_plan.json", "refinement_log.json"],
            next_phases=[WorkflowPhase.ORCHESTRATION_VALIDATION],
            rollback_phases=[WorkflowPhase.ORCHESTRATION_PLANNING],
            validation_criteria=ValidationCriteria(
                surgical_alignment=True,
                success_criteria_clarity=True
            ),
            max_iterations=5,
            parallel_samples=0,
            description="Orchestrator refines plan based on validation"
        ),
        
        # ========== CODING PHASES ==========
        WorkflowPhase.CODING_ASSIGNMENT: PhaseConfig(
            phase=WorkflowPhase.CODING_ASSIGNMENT,
            primary_agent="Orchestrator",
            supporting_agents=["Coder_Agent_1", "Coder_Agent_2", "Coder_Agent_3"],
            valid_tasks=[
                "distribute_coding_tasks",
                "assign_coder_agents",
                "setup_integration_tests"
            ],
            input_artifacts=["orchestration_plan.json", "subtask_definitions/*.md"],
            output_artifacts=["task_assignments.json", "integration_tests/*.py"],
            next_phases=[WorkflowPhase.CODING_IMPLEMENTATION],
            rollback_phases=[WorkflowPhase.ORCHESTRATION_REFINEMENT],
            validation_criteria=ValidationCriteria(
                success_criteria_clarity=True
            ),
            max_iterations=1,
            parallel_samples=0,
            description="Assign coding tasks to parallel agents"
        ),
        
        WorkflowPhase.CODING_IMPLEMENTATION: PhaseConfig(
            phase=WorkflowPhase.CODING_IMPLEMENTATION,
            primary_agent="Coder_Agent",  # Multiple parallel instances
            supporting_agents=[],
            valid_tasks=[
                "implement_subtask",
                "write_unit_tests",
                "document_code",
                "run_local_tests"
            ],
            input_artifacts=["task_assignments.json", "subtask_definitions/*.md"],
            output_artifacts=["src/*.py", "tests/*.py", "docs/*.md"],
            next_phases=[WorkflowPhase.CODING_VALIDATION],
            rollback_phases=[WorkflowPhase.CODING_ASSIGNMENT],
            validation_criteria=ValidationCriteria(
                code_correctness=True
            ),
            max_iterations=1,
            parallel_samples=0,  # But parallel execution
            description="Parallel coders implement their assigned subtasks"
        ),
        
        WorkflowPhase.CODING_VALIDATION: PhaseConfig(
            phase=WorkflowPhase.CODING_VALIDATION,
            primary_agent="Junior_Validator",
            supporting_agents=["Senior_Validator"],
            valid_tasks=[
                "validate_code_correctness",
                "check_success_criteria",
                "verify_integration_readiness",
                "assess_code_quality"
            ],
            input_artifacts=["src/*.py", "tests/*.py", "task_assignments.json"],
            output_artifacts=["code_validation_*.json", "validation_report.md"],
            next_phases=[WorkflowPhase.CODING_INTEGRATION, WorkflowPhase.CODING_IMPLEMENTATION],
            rollback_phases=[WorkflowPhase.CODING_IMPLEMENTATION],
            validation_criteria=ValidationCriteria(
                code_correctness=True,
                success_criteria_clarity=True
            ),
            max_iterations=3,
            parallel_samples=0,
            description="Validate each coder's submission against success criteria"
        ),
        
        WorkflowPhase.CODING_INTEGRATION: PhaseConfig(
            phase=WorkflowPhase.CODING_INTEGRATION,
            primary_agent="Orchestrator",
            supporting_agents=["Senior_Validator"],
            valid_tasks=[
                "run_integration_tests",
                "verify_surgical_alignment",
                "consolidate_codebase",
                "final_code_review"
            ],
            input_artifacts=["src/*.py", "integration_tests/*.py", "integration_spec.json"],
            output_artifacts=["integrated_codebase/", "integration_report.json"],
            next_phases=[WorkflowPhase.EXPERIMENT_SETUP],
            rollback_phases=[WorkflowPhase.CODING_IMPLEMENTATION],
            validation_criteria=ValidationCriteria(
                surgical_alignment=True,
                code_correctness=True
            ),
            max_iterations=2,
            parallel_samples=0,
            description="Verify surgical alignment of parallel components"
        ),
        
        # ========== EXPERIMENT PHASES ==========
        WorkflowPhase.EXPERIMENT_SETUP: PhaseConfig(
            phase=WorkflowPhase.EXPERIMENT_SETUP,
            primary_agent="Experiment_Executor",
            supporting_agents=[],
            valid_tasks=[
                "prepare_experiment_environment",
                "validate_data_sources",
                "setup_logging_infrastructure",
                "create_experiment_manifest"
            ],
            input_artifacts=["integrated_codebase/", "research_plan_v*.md"],
            output_artifacts=["experiment_manifest.json", "logging_config.json"],
            next_phases=[WorkflowPhase.EXPERIMENT_EXECUTION],
            rollback_phases=[WorkflowPhase.CODING_INTEGRATION],
            validation_criteria=ValidationCriteria(
                data_hygiene=True,
                execution_completeness=True
            ),
            max_iterations=1,
            parallel_samples=0,
            description="Prepare for meticulous experiment execution"
        ),
        
        WorkflowPhase.EXPERIMENT_EXECUTION: PhaseConfig(
            phase=WorkflowPhase.EXPERIMENT_EXECUTION,
            primary_agent="Experiment_Executor",
            supporting_agents=[],
            valid_tasks=[
                "execute_experiments",
                "log_experiment_details",
                "capture_raw_results",
                "monitor_execution_health"
            ],
            input_artifacts=["experiment_manifest.json", "integrated_codebase/"],
            output_artifacts=["experiment_logs/*.log", "raw_results/*.csv", "execution_metrics.json"],
            next_phases=[WorkflowPhase.EXPERIMENT_VALIDATION],
            rollback_phases=[WorkflowPhase.EXPERIMENT_SETUP, WorkflowPhase.CODING_INTEGRATION],
            validation_criteria=ValidationCriteria(
                execution_completeness=True,
                data_hygiene=True
            ),
            max_iterations=1,
            parallel_samples=0,
            description="Execute experiments with meticulous logging"
        ),
        
        WorkflowPhase.EXPERIMENT_VALIDATION: PhaseConfig(
            phase=WorkflowPhase.EXPERIMENT_VALIDATION,
            primary_agent="Junior_Validator",
            supporting_agents=["Senior_Validator"],
            valid_tasks=[
                "validate_execution_completeness",
                "check_data_integrity",
                "verify_logging_quality",
                "assess_result_quality"
            ],
            input_artifacts=["experiment_logs/*.log", "raw_results/*.csv", "execution_metrics.json"],
            output_artifacts=["execution_validation.json", "data_quality_report.md"],
            next_phases=[WorkflowPhase.EXPERIMENT_JOURNAL, WorkflowPhase.EXPERIMENT_EXECUTION],
            rollback_phases=[WorkflowPhase.EXPERIMENT_EXECUTION],
            validation_criteria=ValidationCriteria(
                execution_completeness=True,
                data_hygiene=True
            ),
            max_iterations=2,
            parallel_samples=0,
            description="Validate experiment execution meticulousness"
        ),
        
        WorkflowPhase.EXPERIMENT_JOURNAL: PhaseConfig(
            phase=WorkflowPhase.EXPERIMENT_JOURNAL,
            primary_agent="Experiment_Executor",
            supporting_agents=[],
            valid_tasks=[
                "compile_execution_journal",
                "document_observations",
                "note_anomalies",
                "finalize_raw_results"
            ],
            input_artifacts=["experiment_logs/*.log", "execution_validation.json"],
            output_artifacts=["execution_journal.md", "observations.json"],
            next_phases=[WorkflowPhase.RESULTS_PLANNING],
            rollback_phases=[WorkflowPhase.EXPERIMENT_EXECUTION],
            validation_criteria=ValidationCriteria(
                execution_completeness=True
            ),
            max_iterations=1,
            parallel_samples=0,
            description="Create meticulous journal of experiment execution"
        ),
        
        # ========== RESULTS EXTRACTION PHASES ==========
        WorkflowPhase.RESULTS_PLANNING: PhaseConfig(
            phase=WorkflowPhase.RESULTS_PLANNING,
            primary_agent="Orchestrator",
            supporting_agents=[],
            valid_tasks=[
                "plan_results_extraction",
                "define_statistical_analyses",
                "specify_visualization_needs",
                "identify_key_insights"
            ],
            input_artifacts=["raw_results/*.csv", "research_plan_v*.md", "execution_journal.md"],
            output_artifacts=["extraction_plan.json", "analysis_spec.json"],
            next_phases=[WorkflowPhase.RESULTS_EXTRACTION],
            rollback_phases=[WorkflowPhase.EXPERIMENT_JOURNAL],
            validation_criteria=ValidationCriteria(
                statistical_rigor=True,
                result_significance=True
            ),
            max_iterations=1,
            parallel_samples=0,
            description="Plan extraction of key results and insights"
        ),
        
        WorkflowPhase.RESULTS_EXTRACTION: PhaseConfig(
            phase=WorkflowPhase.RESULTS_EXTRACTION,
            primary_agent="Coder_Agent",
            supporting_agents=["Orchestrator"],
            valid_tasks=[
                "implement_extraction_code",
                "run_statistical_tests",
                "generate_visualizations",
                "extract_key_metrics"
            ],
            input_artifacts=["extraction_plan.json", "raw_results/*.csv"],
            output_artifacts=["processed_results/*.json", "visualizations/*.png", "statistical_tests.json"],
            next_phases=[WorkflowPhase.RESULTS_VALIDATION],
            rollback_phases=[WorkflowPhase.RESULTS_PLANNING],
            validation_criteria=ValidationCriteria(
                code_correctness=True,
                statistical_rigor=True
            ),
            max_iterations=1,
            parallel_samples=0,
            description="Extract and process results per extraction plan"
        ),
        
        WorkflowPhase.RESULTS_VALIDATION: PhaseConfig(
            phase=WorkflowPhase.RESULTS_VALIDATION,
            primary_agent="Senior_Validator",
            supporting_agents=["Junior_Validator"],
            valid_tasks=[
                "validate_statistical_correctness",
                "verify_result_significance",
                "check_extraction_completeness",
                "assess_insight_quality"
            ],
            input_artifacts=["processed_results/*.json", "statistical_tests.json", "extraction_plan.json"],
            output_artifacts=["results_validation.json", "significance_report.md"],
            next_phases=[WorkflowPhase.FINAL_ANALYSIS, WorkflowPhase.RESULTS_EXTRACTION],
            rollback_phases=[WorkflowPhase.RESULTS_EXTRACTION],
            validation_criteria=ValidationCriteria(
                statistical_rigor=True,
                result_significance=True
            ),
            max_iterations=2,
            parallel_samples=0,
            description="Validate extracted results for correctness and significance"
        ),
        
        # ========== FINAL SYNTHESIS PHASES ==========
        WorkflowPhase.FINAL_ANALYSIS: PhaseConfig(
            phase=WorkflowPhase.FINAL_ANALYSIS,
            primary_agent="Chief_Researcher",
            supporting_agents=[],
            valid_tasks=[
                "synthesize_findings",
                "identify_novel_insights",
                "assess_statistical_significance",
                "draw_conclusions"
            ],
            input_artifacts=["processed_results/*.json", "execution_journal.md", "research_plan_v*.md"],
            output_artifacts=["analysis_synthesis.md", "key_findings.json"],
            next_phases=[WorkflowPhase.FINAL_REPORT],
            rollback_phases=[WorkflowPhase.RESULTS_VALIDATION],
            validation_criteria=ValidationCriteria(
                statistical_rigor=True,
                novel_insights=True,
                result_significance=True
            ),
            max_iterations=1,
            parallel_samples=0,
            description="Chief Researcher synthesizes all findings"
        ),
        
        WorkflowPhase.FINAL_REPORT: PhaseConfig(
            phase=WorkflowPhase.FINAL_REPORT,
            primary_agent="Chief_Researcher",
            supporting_agents=[],
            valid_tasks=[
                "generate_final_report",
                "create_executive_summary",
                "compile_appendices",
                "prepare_deliverables"
            ],
            input_artifacts=["analysis_synthesis.md", "key_findings.json", "visualizations/*.png"],
            output_artifacts=["final_report.md", "executive_summary.md", "deliverables/"],
            next_phases=[],  # Terminal phase
            rollback_phases=[WorkflowPhase.FINAL_ANALYSIS],
            validation_criteria=ValidationCriteria(
                result_significance=True,
                novel_insights=True
            ),
            max_iterations=1,
            parallel_samples=0,
            description="Generate comprehensive final report with all insights"
        ),
        
        # ========== ERROR HANDLING PHASES ==========
        WorkflowPhase.ERROR: PhaseConfig(
            phase=WorkflowPhase.ERROR,
            primary_agent="System",
            supporting_agents=[],
            valid_tasks=["log_error", "capture_state", "determine_recovery"],
            input_artifacts=["error_context.json"],
            output_artifacts=["error_log.json", "recovery_plan.json"],
            next_phases=[WorkflowPhase.RECOVERY],
            rollback_phases=[],
            validation_criteria=ValidationCriteria(),
            max_iterations=1,
            parallel_samples=0,
            description="Error capture and recovery planning"
        ),
        
        WorkflowPhase.RECOVERY: PhaseConfig(
            phase=WorkflowPhase.RECOVERY,
            primary_agent="System",
            supporting_agents=["Orchestrator"],
            valid_tasks=["restore_checkpoint", "rollback_phase", "reinitialize_agents"],
            input_artifacts=["recovery_plan.json"],
            output_artifacts=["recovery_log.json"],
            next_phases=[
                WorkflowPhase.RESEARCH_PLANNING,
                WorkflowPhase.ORCHESTRATION_PLANNING,
                WorkflowPhase.CODING_IMPLEMENTATION,
                WorkflowPhase.EXPERIMENT_EXECUTION
            ],
            rollback_phases=[],
            validation_criteria=ValidationCriteria(),
            max_iterations=1,
            parallel_samples=0,
            description="Execute recovery to safe rollback point"
        )
    }
    
    @classmethod
    def get_phase_config(cls, phase: WorkflowPhase) -> Optional[PhaseConfig]:
        """Get configuration for a phase."""
        return cls.PHASE_CONFIGS.get(phase)
    
    @classmethod
    def get_agent_phases(cls, agent_name: str) -> List[WorkflowPhase]:
        """Get all phases where an agent is primary or supporting."""
        phases = []
        for phase, config in cls.PHASE_CONFIGS.items():
            if config.primary_agent == agent_name or agent_name in config.supporting_agents:
                phases.append(phase)
        return phases
    
    @classmethod
    def get_validation_loop_phases(cls) -> Dict[str, List[WorkflowPhase]]:
        """Get all validation loop phases grouped by type."""
        return {
            'research': [
                WorkflowPhase.RESEARCH_PLANNING,
                WorkflowPhase.RESEARCH_VALIDATION,
                WorkflowPhase.RESEARCH_REFINEMENT,
                WorkflowPhase.RESEARCH_PARALLEL_VALIDATION
            ],
            'orchestration': [
                WorkflowPhase.ORCHESTRATION_PLANNING,
                WorkflowPhase.ORCHESTRATION_VALIDATION,
                WorkflowPhase.ORCHESTRATION_REFINEMENT
            ],
            'coding': [
                WorkflowPhase.CODING_IMPLEMENTATION,
                WorkflowPhase.CODING_VALIDATION
            ],
            'experiment': [
                WorkflowPhase.EXPERIMENT_EXECUTION,
                WorkflowPhase.EXPERIMENT_VALIDATION
            ],
            'results': [
                WorkflowPhase.RESULTS_EXTRACTION,
                WorkflowPhase.RESULTS_VALIDATION
            ]
        }
    
    @classmethod
    def can_transition(cls, from_phase: WorkflowPhase, to_phase: WorkflowPhase) -> bool:
        """Check if a phase transition is valid."""
        config = cls.get_phase_config(from_phase)
        if not config:
            return False
        return to_phase in config.next_phases or to_phase in config.rollback_phases
    
    @classmethod
    def get_rollback_target(cls, current_phase: WorkflowPhase, error_type: str = None) -> Optional[WorkflowPhase]:
        """Determine the best rollback target based on current phase and error type."""
        config = cls.get_phase_config(current_phase)
        if not config or not config.rollback_phases:
            return WorkflowPhase.ERROR
        
        # Logic to choose rollback based on error type
        if error_type == "validation_failure":
            # Go back to the planning phase of current loop
            if "VALIDATION" in current_phase.name:
                # Go back to the corresponding planning phase
                phase_prefix = current_phase.name.split('_')[0]
                planning_phase = f"{phase_prefix}_PLANNING"
                try:
                    return WorkflowPhase[planning_phase]
                except KeyError:
                    pass
        
        # Default to first rollback phase
        return config.rollback_phases[0] if config.rollback_phases else WorkflowPhase.ERROR
    
    @classmethod
    def get_phase_by_task(cls, task_name: str) -> Optional[WorkflowPhase]:
        """Find which phase a task belongs to."""
        for phase, config in cls.PHASE_CONFIGS.items():
            if task_name in config.valid_tasks:
                return phase
        return None
    
    @classmethod
    def get_required_validations(cls, phase: WorkflowPhase) -> ValidationCriteria:
        """Get the validation criteria required for a phase."""
        config = cls.get_phase_config(phase)
        return config.validation_criteria if config else ValidationCriteria()
    
    @classmethod
    def is_terminal_phase(cls, phase: WorkflowPhase) -> bool:
        """Check if a phase is terminal (no next phases)."""
        config = cls.get_phase_config(phase)
        return config and len(config.next_phases) == 0
    
    @classmethod
    def get_parallel_config(cls, phase: WorkflowPhase) -> Tuple[int, int]:
        """Get parallel configuration (max_iterations, parallel_samples) for a phase."""
        config = cls.get_phase_config(phase)
        if config:
            return config.max_iterations, config.parallel_samples
        return 1, 0


# Global enhanced phase manager instance
enhanced_phase_manager = EnhancedPhaseManager()