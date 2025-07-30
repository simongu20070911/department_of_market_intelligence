# /department_of_market_intelligence/utils/directory_manager.py
"""Utility for creating the standardized directory structure."""

import os
from typing import List


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
    # Define all required subdirectories
    required_dirs = [
        # Planning directories
        f"{outputs_dir}/planning",
        f"{outputs_dir}/planning/critiques", 
        
        # Workspace directories
        f"{outputs_dir}/workspace",
        f"{outputs_dir}/workspace/scripts",
        f"{outputs_dir}/workspace/notebooks",
        f"{outputs_dir}/workspace/src",
        f"{outputs_dir}/workspace/tests",
        
        # Results directories
        f"{outputs_dir}/results",
        f"{outputs_dir}/results/deliverables",
        f"{outputs_dir}/results/deliverables/presentations",
        f"{outputs_dir}/results/charts",
        
        # Data directories
        f"{outputs_dir}/data",
        f"{outputs_dir}/data/external",
        f"{outputs_dir}/data/processed",
        f"{outputs_dir}/data/raw",
    ]
    
    # Create all directories
    for dir_path in required_dirs:
        os.makedirs(dir_path, exist_ok=True)
    
    print(f"📁 Created complete directory structure in: {outputs_dir}")
    print(f"   • {len(required_dirs)} subdirectories created")


def validate_directory_structure(outputs_dir: str) -> List[str]:
    """Validate that the directory structure is complete.
    
    Args:
        outputs_dir: The base outputs directory path
        
    Returns:
        List of missing directories (empty if all exist)
    """
    required_dirs = [
        f"{outputs_dir}/planning",
        f"{outputs_dir}/planning/critiques", 
        f"{outputs_dir}/workspace/scripts",
        f"{outputs_dir}/workspace/notebooks",
        f"{outputs_dir}/workspace/src",
        f"{outputs_dir}/workspace/tests",
        f"{outputs_dir}/results/deliverables",
        f"{outputs_dir}/results/deliverables/presentations",
        f"{outputs_dir}/results/charts",
        f"{outputs_dir}/data/external",
        f"{outputs_dir}/data/processed",
        f"{outputs_dir}/data/raw",
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
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