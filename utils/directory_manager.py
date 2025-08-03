# /department_of_market_intelligence/utils/directory_manager.py
"""Utility for creating the standardized directory structure."""

import os
from typing import List

# Define all required subdirectories as a constant for reuse
DIRECTORY_STRUCTURE = [
    # Planning directories
    "planning",
    "planning/critiques", 
    
    # Workspace directories
    "workspace",
    "workspace/scripts",
    "workspace/notebooks",
    "workspace/src",
    "workspace/tests",
    
    # Results directories
    "results",
    "results/deliverables",
    "results/deliverables/presentations",
    "results/charts",
    
    # Data directories
    "data",
    "data/external",
    "data/processed",
    "data/raw",
]

def create_task_directory_structure(outputs_dir: str) -> None:
    """Create the complete directory structure for a task.
    
    Creates the exact structure specified in DIRECTORY_STRUCTURE_SPEC:
    
    outputs_dir/
    ├── planning/
    │   └── critiques/
    ├── workspace/
    │   ├── scripts/
    │   ├── notebooks/
    │   ├── src/
    │   └── tests/
    ├── results/
    │   ├── deliverables/
    │   │   └── presentations/
    │   └── charts/
    └── data/
        ├── external/
        ├── processed/
        └── raw/
    
    Args:
        outputs_dir: The base outputs directory path
    """
    # Create all directories from the constant
    for rel_path in DIRECTORY_STRUCTURE:
        dir_path = os.path.join(outputs_dir, rel_path)
        os.makedirs(dir_path, exist_ok=True)
    
    print(f"📁 Created complete directory structure in: {outputs_dir}")
    print(f"   • {len(DIRECTORY_STRUCTURE)} subdirectories created")


def validate_directory_structure(outputs_dir: str) -> List[str]:
    """Validate that the directory structure is complete.
    
    Args:
        outputs_dir: The base outputs directory path
        
    Returns:
        List of missing directories (empty if all exist)
    """
    missing_dirs = []
    for rel_path in DIRECTORY_STRUCTURE:
        dir_path = os.path.join(outputs_dir, rel_path)
        if not os.path.exists(dir_path):
            missing_dirs.append(dir_path)
    
    return missing_dirs


def get_directory_structure_summary(outputs_dir: str) -> str:
    """Get a summary of the directory structure status.
    
    Args:
        outputs_dir: The base outputs directory path
        
    Returns:
        Formatted string summarizing the directory structure
    """
    missing = validate_directory_structure(outputs_dir)
    
    if not missing:
        return f"✅ Complete directory structure exists in: {outputs_dir}"
    else:
        return f"❌ Missing {len(missing)} directories in: {outputs_dir}\n   Missing: {missing[:3]}{'...' if len(missing) > 3 else ''}"