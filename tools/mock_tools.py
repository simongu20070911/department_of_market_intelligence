# /department_of_market_intelligence/tools/mock_tools.py
"""Enhanced mock tools for comprehensive dry run testing - simulates MCP Desktop Commander functionality."""

from google.adk.tools import FunctionTool
from typing import Dict, Any, Set
import os
from pathlib import Path
try:
    from .. import config
except ImportError:
    # Handle direct execution case
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    import config

# Global state for tracking dry run operations
class DryRunFileSystem:
    """Simulates a file system for comprehensive dry run testing."""
    
    def __init__(self):
        self.files: Dict[str, str] = {}  # path -> content
        self.directories: Set[str] = set()
        self.operations_log: list = []
        self.path_consistency_checks: list = []
        
    def reset(self):
        """Reset the dry run file system."""
        self.files.clear()
        self.directories.clear()
        self.operations_log.clear()
        self.path_consistency_checks.clear()
        
    def validate_path_consistency(self, path: str, operation: str) -> bool:
        """Validate that the path uses the correct task-specific directory."""
        expected_task_dir = f"outputs/{config.TASK_ID}"
        
        # Check if this is a task-specific file path
        if "/outputs/" in path and not path.endswith("sample_research_task.md"):
            if expected_task_dir not in path and "default_research_task" in path:
                issue = f"❌ PATH INCONSISTENCY: {operation} using old task path: {path}"
                self.path_consistency_checks.append(issue)
                print(issue)
                return False
            elif expected_task_dir in path:
                success = f"✅ PATH CONSISTENT: {operation} using correct task path: {path}"
                self.path_consistency_checks.append(success)
                print(success)
                return True
        
        return True  # Non-task files are OK
        
    def log_operation(self, operation: str, path: str, details: str = ""):
        """Log a file operation for testing validation."""
        self.operations_log.append({
            "operation": operation,
            "path": path,
            "details": details,
            "task_id": config.TASK_ID
        })
        
    def create_task_directory_structure(self, task_id: str) -> None:
        """Create the complete directory structure for a task."""
        base_dir = f"outputs/{task_id}"
        
        # Define the required directory structure
        required_dirs = [
            base_dir,
            f"{base_dir}/planning",
            f"{base_dir}/planning/critiques", 
            f"{base_dir}/workspace",
            f"{base_dir}/workspace/scripts",
            f"{base_dir}/workspace/notebooks",
            f"{base_dir}/workspace/src",
            f"{base_dir}/workspace/tests",
            f"{base_dir}/results",
            f"{base_dir}/results/deliverables",
            f"{base_dir}/results/deliverables/presentations",
            f"{base_dir}/results/charts",
            f"{base_dir}/data",
            f"{base_dir}/data/external", 
            f"{base_dir}/data/processed",
            f"{base_dir}/data/raw"
        ]
        
        # Create all directories
        for dir_path in required_dirs:
            self.directories.add(dir_path)
            self.log_operation("AUTO_CREATE_DIR", dir_path, "Required directory structure")
            
        print(f"[DRY RUN] 🏗️  Created complete directory structure for task: {task_id}")
        print(f"[DRY RUN] 📁 Created {len(required_dirs)} directories")
        
    def get_directory_structure_summary(self, task_id: str) -> str:
        """Get a tree-like summary of the created directory structure."""
        base_dir = f"outputs/{task_id}"
        dirs_for_task = [d for d in sorted(self.directories) if d.startswith(base_dir)]
        
        summary = f"\n🌳 DIRECTORY STRUCTURE for {task_id}:\n"
        summary += f"outputs/{task_id}/\n"
        
        for dir_path in dirs_for_task:
            if dir_path == base_dir:
                continue
            relative_path = dir_path.replace(f"{base_dir}/", "")
            depth = relative_path.count("/")
            indent = "  " * (depth + 1)
            folder_name = relative_path.split("/")[-1]
            summary += f"{indent}├── {folder_name}/\n"
            
        return summary

    def get_path_summary(self) -> str:
        """Get a summary of all path operations for testing."""
        summary = "\n📋 DRY RUN PATH SUMMARY:\n"
        summary += f"   Task ID: {config.TASK_ID}\n"
        summary += f"   Expected path pattern: outputs/{config.TASK_ID}/\n\n"
        
        for check in self.path_consistency_checks:
            summary += f"   {check}\n"
            
        summary += f"\n📊 Operations performed: {len(self.operations_log)}\n"
        for op in self.operations_log:
            summary += f"   - {op['operation']}: {op['path']}\n"
            
        # Add directory structure summary
        summary += self.get_directory_structure_summary(config.TASK_ID)
            
        return summary

# Global instance
dry_run_fs = DryRunFileSystem()

async def read_file(path: str) -> str:
    """Enhanced mock read_file tool with path validation."""
    dry_run_fs.validate_path_consistency(path, "READ")
    dry_run_fs.log_operation("READ", path)
    
    # Special case for the research task file
    if "sample_research_task.md" in path:
        content = """# Research Task: Analyze Market Microstructure Evolution

## Objective
Conduct a comprehensive analysis of how market microstructure has evolved from 2020-2024, 
focusing on the impact of zero-commission trading, payment for order flow (PFOF), 
and the rise of retail trading platforms.

## Key Areas to Investigate
1. Changes in bid-ask spreads across different asset classes
2. Market depth and liquidity provision mechanisms
3. Impact of gamification on retail trading behavior
4. Regulatory responses and their effectiveness

## Expected Deliverables
- Quantitative analysis with statistical significance testing
- Visualization of key trends
- Policy recommendations based on findings
"""
        dry_run_fs.files[path] = content
        print(f"[DRY RUN] ✅ READ: {path} (research task)")
        return content
    
    # Check if file exists in our dry run filesystem
    if path in dry_run_fs.files:
        content = dry_run_fs.files[path]
        print(f"[DRY RUN] ✅ READ: {path} ({len(content)} chars)")
        return content
    
    # Simulate reading critique files that might exist
    if "critique" in path:
        mock_critique = f"[DRY RUN] Mock critique content for validation testing from {path}"
        dry_run_fs.files[path] = mock_critique
        print(f"[DRY RUN] ✅ READ: {path} (mock critique)")
        return mock_critique
        
    print(f"[DRY RUN] ❌ READ: File not found {path}")
    return f"[DRY RUN] ERROR: File not found: {path}"

async def write_file(path: str, content: str, mode: str = "rewrite") -> str:
    """Enhanced mock write_file tool with path validation and state tracking."""
    dry_run_fs.validate_path_consistency(path, "WRITE")
    dry_run_fs.log_operation("WRITE", path, f"{len(content)} chars, mode={mode}")
    
    # Ensure all parent directories exist in our mock filesystem
    dir_path = str(Path(path).parent)
    # Create all parent directories
    parts = Path(dir_path).parts
    for i in range(len(parts)):
        parent_path = str(Path(*parts[:i+1]))
        if parent_path and parent_path != '.':
            dry_run_fs.directories.add(parent_path)
    
    # Store the content in our mock filesystem
    if mode == "append" and path in dry_run_fs.files:
        dry_run_fs.files[path] += content
    else:
        dry_run_fs.files[path] = content
    
    print(f"[DRY RUN] ✅ WRITE: {path} ({len(content)} chars, mode={mode})")
    
    # Special validation for key files
    if "research_plan" in path:
        print(f"[DRY RUN] 📋 RESEARCH PLAN: Version tracked in {path}")
    elif "critique" in path:
        print(f"[DRY RUN] 🔍 CRITIQUE: Validation feedback in {path}")
    elif "final_report" in path:
        print(f"[DRY RUN] 📊 FINAL REPORT: Delivered to {path}")
        
    return f"[DRY RUN] Successfully wrote to {path}"

async def create_directory(path: str) -> str:
    """Enhanced mock create_directory tool with tracking."""
    dry_run_fs.validate_path_consistency(path, "CREATE_DIR")
    dry_run_fs.log_operation("CREATE_DIR", path)
    dry_run_fs.directories.add(path)
    
    print(f"[DRY RUN] ✅ CREATE_DIR: {path}")
    return f"[DRY RUN] Created directory {path}"

async def list_directory(path: str) -> str:
    """Enhanced mock list_directory tool."""
    dry_run_fs.log_operation("LIST_DIR", path)
    
    # Return files that would be in this directory
    files_in_dir = [f for f in dry_run_fs.files.keys() if f.startswith(path)]
    dirs_in_dir = [d for d in dry_run_fs.directories if d.startswith(path) and d != path]
    
    mock_listing = f"[DRY RUN] Contents of {path}:\n"
    for d in dirs_in_dir:
        mock_listing += f"  [DIR] {d}\n"
    for f in files_in_dir:
        mock_listing += f"  [FILE] {f}\n"
        
    print(f"[DRY RUN] ✅ LIST_DIR: {path} ({len(files_in_dir)} files, {len(dirs_in_dir)} dirs)")
    return mock_listing

async def search_files(path: str, pattern: str) -> str:
    """Enhanced mock search_files tool."""
    dry_run_fs.log_operation("SEARCH", path, f"pattern={pattern}")
    
    # Find matching files in our mock filesystem
    matches = [f for f in dry_run_fs.files.keys() if pattern.lower() in f.lower() and f.startswith(path)]
    
    print(f"[DRY RUN] ✅ SEARCH: Found {len(matches)} files matching '{pattern}' in {path}")
    return f"[DRY RUN] Found {len(matches)} files matching '{pattern}' in {path}: {matches}"

def get_dry_run_summary() -> str:
    """Get comprehensive dry run testing summary."""
    return dry_run_fs.get_path_summary()

def reset_dry_run_state():
    """Reset dry run state for clean testing."""
    dry_run_fs.reset()
    print("[DRY RUN] 🔄 File system state reset for clean testing")

def initialize_task_directory_structure(task_id: str = None):
    """Initialize the complete directory structure for a task."""
    if task_id is None:
        task_id = config.TASK_ID
    dry_run_fs.create_task_directory_structure(task_id)

def create_test_output_directory():
    """Create a test output directory to compare with model structure."""
    test_task_id = "directory_structure_test"
    print(f"\n🧪 CREATING TEST DIRECTORY STRUCTURE for {test_task_id}")
    print("=" * 60)
    
    # Reset state and create the directory structure
    reset_dry_run_state()
    initialize_task_directory_structure(test_task_id)
    
    # Create some sample files to test the structure
    sample_files = [
        f"outputs/{test_task_id}/planning/research_plan_v0.md",
        f"outputs/{test_task_id}/planning/research_plan_v1.md", 
        f"outputs/{test_task_id}/planning/critiques/junior_critique_v0.md",
        f"outputs/{test_task_id}/planning/critiques/senior_critique_v0.md",
        f"outputs/{test_task_id}/planning/implementation_manifest.json",
        f"outputs/{test_task_id}/workspace/scripts/results_extraction.py",
        f"outputs/{test_task_id}/results/deliverables/final_report.md",
        f"outputs/{test_task_id}/results/execution_results.json"
    ]
    
    # Simulate creating these files
    for file_path in sample_files:
        dry_run_fs.files[file_path] = f"[TEST CONTENT] Sample content for {file_path}"
        dry_run_fs.log_operation("TEST_WRITE", file_path, "Sample file for structure testing")
    
    print(f"[DRY RUN] 📝 Created {len(sample_files)} sample files")
    print(dry_run_fs.get_directory_structure_summary(test_task_id))
    
    return test_task_id

def compare_with_model_structure():
    """Compare the created structure with the model structure."""
    print("\n🔍 COMPARING WITH MODEL STRUCTURE")
    print("=" * 50)
    
    model_structure_dirs = [
        "planning",
        "planning/critiques", 
        "workspace",
        "workspace/scripts",
        "workspace/notebooks",
        "workspace/src", 
        "workspace/tests",
        "results",
        "results/deliverables",
        "results/deliverables/presentations",
        "results/charts",
        "data",
        "data/external",
        "data/processed", 
        "data/raw"
    ]
    
    test_task_id = "directory_structure_test"
    base_dir = f"outputs/{test_task_id}"
    created_dirs = [d.replace(f"{base_dir}/", "") for d in dry_run_fs.directories if d.startswith(f"{base_dir}/") and d != base_dir]
    
    print(f"✅ Expected directories: {len(model_structure_dirs)}")
    print(f"✅ Created directories: {len(created_dirs)}")
    
    missing = set(model_structure_dirs) - set(created_dirs)
    extra = set(created_dirs) - set(model_structure_dirs)
    
    if not missing and not extra:
        print("🎉 PERFECT MATCH! Directory structure matches model exactly.")
    else:
        if missing:
            print(f"❌ Missing directories: {missing}")
        if extra:
            print(f"⚠️  Extra directories: {extra}")
    
    return len(missing) == 0 and len(extra) == 0

# Create the enhanced mock toolset
mock_desktop_commander_toolset = [
    FunctionTool(read_file),
    FunctionTool(write_file),
    FunctionTool(create_directory),
    FunctionTool(list_directory),
    FunctionTool(search_files),
]