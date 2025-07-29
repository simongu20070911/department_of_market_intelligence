# utils/task_loader.py

import os
from typing import Dict, Any, Tuple, Optional
from .. import config

def load_task_description(task_id: str, tasks_dir: str = None) -> str:
    """
    Loads the markdown content of a research task from its file.

    Args:
        task_id: The identifier of the task (e.g., 'sample_research_task').
        tasks_dir: The path to the directory containing task files. If None, uses config.TASKS_DIR.

    Returns:
        The string content of the task file.
    
    Raises:
        FileNotFoundError: If the task file doesn't exist.
        ValueError: If task_id is empty or None.
    """
    if not task_id:
        raise ValueError("Task ID cannot be empty or None")
    
    # Use provided tasks_dir or fall back to config
    if tasks_dir is None:
        tasks_dir = config.TASKS_DIR
    
    # Make tasks_dir absolute if it's relative
    if not os.path.isabs(tasks_dir):
        # Get the directory where this module is located
        module_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        tasks_dir = os.path.join(module_dir, tasks_dir)
    
    # Construct the full path to the task file
    task_filename = f"{task_id}.md"
    task_file_path = os.path.join(tasks_dir, task_filename)
    
    # Check if the file exists
    if not os.path.exists(task_file_path):
        available_tasks = list_available_tasks(tasks_dir)
        raise FileNotFoundError(
            f"Task file '{task_filename}' not found in '{tasks_dir}'. "
            f"Available tasks: {available_tasks}"
        )
    
    # Read and return the file content
    try:
        with open(task_file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        if not content:
            raise ValueError(f"Task file '{task_filename}' is empty")
        
        return content
    
    except Exception as e:
        raise RuntimeError(f"Failed to read task file '{task_filename}': {str(e)}")

def list_available_tasks(tasks_dir: str = None) -> list:
    """
    Lists all available task files in the tasks directory.

    Args:
        tasks_dir: The path to the directory containing task files. If None, uses config.TASKS_DIR.

    Returns:
        A list of task IDs (without .md extension) available in the tasks directory.
    """
    if tasks_dir is None:
        tasks_dir = config.TASKS_DIR
    
    # Make tasks_dir absolute if it's relative
    if not os.path.isabs(tasks_dir):
        module_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        tasks_dir = os.path.join(module_dir, tasks_dir)
    
    if not os.path.exists(tasks_dir):
        return []
    
    tasks = []
    for filename in os.listdir(tasks_dir):
        if filename.endswith('.md'):
            task_id = filename[:-3]  # Remove .md extension
            tasks.append(task_id)
    
    return sorted(tasks)

def validate_task_id(task_id: str, tasks_dir: str = None) -> bool:
    """
    Validates that a task ID corresponds to an existing task file.

    Args:
        task_id: The task identifier to validate.
        tasks_dir: The path to the directory containing task files. If None, uses config.TASKS_DIR.

    Returns:
        True if the task exists, False otherwise.
    """
    if not task_id:
        return False
    
    try:
        load_task_description(task_id, tasks_dir)
        return True
    except (FileNotFoundError, ValueError, RuntimeError):
        return False

def get_task_file_path(task_id: str, tasks_dir: str = None) -> str:
    """
    Returns the full path to a task file.

    Args:
        task_id: The task identifier.
        tasks_dir: The path to the directory containing task files. If None, uses config.TASKS_DIR.

    Returns:
        The full absolute path to the task file.
    
    Raises:
        ValueError: If task_id is empty or None.
    """
    if not task_id:
        raise ValueError("Task ID cannot be empty or None")
    
    if tasks_dir is None:
        tasks_dir = config.TASKS_DIR
    
    # Make tasks_dir absolute if it's relative
    if not os.path.isabs(tasks_dir):
        module_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        tasks_dir = os.path.join(module_dir, tasks_dir)
    
    task_filename = f"{task_id}.md"
    return os.path.join(tasks_dir, task_filename)

def get_task_metadata(task_id: str, tasks_dir: str = None) -> Dict[str, Any]:
    """
    Extracts metadata from a task file (if any frontmatter exists).

    Args:
        task_id: The task identifier.
        tasks_dir: The path to the directory containing task files. If None, uses config.TASKS_DIR.

    Returns:
        A dictionary containing task metadata. Always includes 'task_id' and 'file_path'.
    """
    task_content = load_task_description(task_id, tasks_dir)
    task_file_path = get_task_file_path(task_id, tasks_dir)
    
    metadata = {
        'task_id': task_id,
        'file_path': task_file_path,
        'content_length': len(task_content),
        'line_count': task_content.count('\n') + 1 if task_content else 0
    }
    
    # Check for YAML frontmatter (between --- delimiters)
    if task_content.startswith('---'):
        try:
            end_delimiter = task_content.find('\n---\n', 3)
            if end_delimiter != -1:
                frontmatter = task_content[3:end_delimiter].strip()
                # Simple key: value parsing (could use yaml library for complex cases)
                for line in frontmatter.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        metadata[key.strip()] = value.strip()
        except Exception:
            # If frontmatter parsing fails, just continue with basic metadata
            pass
    
    return metadata

def create_task_loading_summary() -> str:
    """
    Creates a summary of the task loading configuration and available tasks.
    
    Returns:
        A formatted string with task loading information.
    """
    summary_lines = [
        "📋 TASK LOADING CONFIGURATION",
        "=" * 50,
        f"• Current Task ID: {config.TASK_ID}",
        f"• Tasks Directory: {config.TASKS_DIR}",
        f"• Outputs Base Dir: {config.OUTPUTS_BASE_DIR}",
        "",
        "📁 AVAILABLE TASKS:",
    ]
    
    try:
        available_tasks = list_available_tasks()
        if available_tasks:
            for task in available_tasks:
                marker = "✅" if task == config.TASK_ID else "📄"
                summary_lines.append(f"  {marker} {task}")
        else:
            summary_lines.append("  (No tasks found)")
    except Exception as e:
        summary_lines.append(f"  ❌ Error listing tasks: {e}")
    
    summary_lines.extend([
        "",
        "🔧 VALIDATION:",
        f"• Current task valid: {validate_task_id(config.TASK_ID)}",
        f"• Tasks dir exists: {os.path.exists(config.TASKS_DIR)}",
        f"• Outputs dir exists: {os.path.exists(config.OUTPUTS_BASE_DIR)}",
    ])
    
    return "\n".join(summary_lines)