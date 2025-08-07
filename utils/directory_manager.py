import os
from .. import config

def get_research_plan_path(task_id: str, version: int) -> str:
    """Gets the path for a research plan of a specific version."""
    return os.path.join(config.get_outputs_dir(task_id), "planning", f"research_plan_v{version}.md")

def get_critique_path(task_id: str, version: int, role: str) -> str:
    """Gets the path for a critique file."""
    return os.path.join(config.get_outputs_dir(task_id), "planning", "critiques", f"{role}_critique_v{version}.md")

def get_implementation_manifest_path(task_id: str) -> str:
    """Gets the path for the implementation manifest."""
    return os.path.join(config.get_outputs_dir(task_id), "implementation", "orchestration_plan.json")

def get_execution_journal_path(task_id: str) -> str:
    """Gets the path for the execution journal."""
    return os.path.join(config.get_outputs_dir(task_id), "execution", "execution_journal.md")

def get_results_extraction_script_path(task_id: str) -> str:
    """Gets the path for the results extraction script."""
    return os.path.join(config.get_outputs_dir(task_id), "workspace", "scripts", "results_extraction.py")

def get_final_report_path(task_id: str) -> str:
    """Gets the path for the final report."""
    return os.path.join(config.get_outputs_dir(task_id), "results", "deliverables", "final_report.md")

def get_parallel_validation_path(task_id: str, version: int, index: int) -> str:
    """Gets the path for a parallel validation file."""
    return os.path.join(config.get_outputs_dir(task_id), "planning", "critiques", f"parallel_validation_{index}_v{version}.md")

def get_coder_output_path(task_id: str, sub_task_id: str, version: int) -> str:
    """Gets the path for a coder's output for a specific sub-task and version."""
    return os.path.join(config.get_outputs_dir(task_id), "implementation", "code", f"{sub_task_id}_v{version}.py")