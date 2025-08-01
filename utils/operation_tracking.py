# /department_of_market_intelligence/utils/operation_tracking.py
"""Operation tracking decorators and context managers for fine-grained recovery."""

import functools
import inspect
from typing import Callable, Any, Dict, List, Optional
from contextlib import contextmanager

from .micro_checkpoint_manager import (
    micro_checkpoint_manager, 
    OperationStep, 
    OperationProgress
)
from .. import config


def recoverable_operation(operation_id: str = None, 
                         expected_outputs: List[str] = None,
                         timeout_seconds: int = None,
                         max_retries: int = 3):
    """Decorator to make a function recoverable with micro-checkpoints.
    
    Usage:
        @recoverable_operation(
            operation_id="generate_research_plan",
            expected_outputs=["research_plan_v1.md"],
            timeout_seconds=300,
            max_retries=2
        )
        async def generate_plan(self, ctx, requirements):
            # Function implementation
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate operation ID if not provided
            nonlocal operation_id
            if operation_id is None:
                operation_id = f"{func.__name__}_{int(time.time())}"
            
            # Extract agent name from self if available
            agent_name = "Unknown"
            if args and hasattr(args[0], '__class__'):
                agent_name = args[0].__class__.__name__
            
            # Create operation step
            step = OperationStep(
                step_id=f"{operation_id}_main",
                operation_type="function_execution",
                step_name=func.__name__,
                input_state={
                    "args": str(args[1:]),  # Skip self
                    "kwargs": kwargs
                },
                expected_outputs=expected_outputs or [],
                timeout_seconds=timeout_seconds,
                max_retries=max_retries
            )
            
            # Start operation tracking
            micro_checkpoint_manager.start_operation(
                operation_id=operation_id,
                agent_name=agent_name,
                steps=[step]
            )
            
            # Execute with step context
            with micro_checkpoint_manager.step_context(step):
                result = await func(*args, **kwargs)
                return result
        
        return wrapper
    return decorator


@contextmanager
def tracked_operation(operation_id: str, 
                     agent_name: str,
                     steps: List[OperationStep],
                     operation_state: Dict[str, Any] = None):
    """Context manager for tracking multi-step operations.
    
    Usage:
        steps = [
            OperationStep("step1", "file_generation", "Create analysis script", {...}),
            OperationStep("step2", "execution", "Run analysis", {...}),
            OperationStep("step3", "validation", "Validate results", {...})
        ]
        
        with tracked_operation("analyze_data", "ExperimentExecutor", steps) as tracker:
            for step in steps:
                with tracker.step_context(step):
                    # Execute step logic
                    pass
    """
    # Start the operation
    actual_operation_id = micro_checkpoint_manager.start_operation(
        operation_id=operation_id,
        agent_name=agent_name,
        steps=steps,
        operation_state=operation_state
    )
    
    try:
        yield micro_checkpoint_manager
    finally:
        # Operation completed or failed
        progress = micro_checkpoint_manager.operation_registry.get(actual_operation_id)
        if progress:
            print(f"🏁 Operation {operation_id} finished:")
            print(f"   ✅ Completed: {len(progress.completed_steps)}/{progress.total_steps}")
            print(f"   ❌ Failed: {len(progress.failed_steps)}")


class OperationBuilder:
    """Builder pattern for creating complex operations with multiple steps."""
    
    def __init__(self, operation_id: str, agent_name: str):
        self.operation_id = operation_id
        self.agent_name = agent_name
        self.steps: List[OperationStep] = []
        self.operation_state: Dict[str, Any] = {}
    
    def add_step(self, 
                 step_id: str,
                 operation_type: str,
                 step_name: str,
                 input_state: Dict[str, Any],
                 expected_outputs: List[str] = None,
                 timeout_seconds: int = None,
                 max_retries: int = 3) -> 'OperationBuilder':
        """Add a step to the operation."""
        step = OperationStep(
            step_id=step_id,
            operation_type=operation_type,
            step_name=step_name,
            input_state=input_state,
            expected_outputs=expected_outputs or [],
            timeout_seconds=timeout_seconds,
            max_retries=max_retries
        )
        self.steps.append(step)
        return self
    
    def set_state(self, key: str, value: Any) -> 'OperationBuilder':
        """Set operation state variable."""
        self.operation_state[key] = value
        return self
    
    def build(self) -> Dict[str, Any]:
        """Build the operation configuration."""
        return {
            "operation_id": self.operation_id,
            "agent_name": self.agent_name,
            "steps": self.steps,
            "operation_state": self.operation_state
        }
    
    @contextmanager
    def execute(self):
        """Execute the built operation with tracking."""
        config = self.build()
        with tracked_operation(**config) as tracker:
            yield tracker, self.steps


def create_file_generation_operation(operation_id: str, 
                                   agent_name: str,
                                   files_to_generate: List[Dict[str, Any]]) -> OperationBuilder:
    """Create a file generation operation with individual steps for each file."""
    builder = OperationBuilder(operation_id, agent_name)
    
    for i, file_info in enumerate(files_to_generate):
        builder.add_step(
            step_id=f"generate_file_{i}",
            operation_type="file_generation", 
            step_name=f"Generate {file_info['filename']}",
            input_state=file_info,
            expected_outputs=[file_info['filename']],
            timeout_seconds=file_info.get('timeout', 180),
            max_retries=file_info.get('max_retries', 2)
        )
    
    return builder


def create_experiment_operation(operation_id: str,
                              agent_name: str,
                              experiment_configs: List[Dict[str, Any]]) -> OperationBuilder:
    """Create an experiment execution operation with steps for each experiment."""
    builder = OperationBuilder(operation_id, agent_name)
    
    for i, exp_config in enumerate(experiment_configs):
        builder.add_step(
            step_id=f"experiment_{i}",
            operation_type="experiment_execution",
            step_name=f"Run {exp_config.get('name', f'Experiment {i}')}",
            input_state=exp_config,
            expected_outputs=exp_config.get('expected_outputs', []),
            timeout_seconds=exp_config.get('timeout', 600),  # 10 minutes default
            max_retries=exp_config.get('max_retries', 1)
        )
    
    return builder


def create_data_processing_operation(operation_id: str,
                                   agent_name: str,
                                   processing_steps: List[Dict[str, Any]]) -> OperationBuilder:
    """Create a data processing operation with individual processing steps."""
    builder = OperationBuilder(operation_id, agent_name)
    
    for i, step_config in enumerate(processing_steps):
        builder.add_step(
            step_id=f"process_step_{i}",
            operation_type="data_processing",
            step_name=step_config.get('name', f'Processing Step {i}'),
            input_state=step_config,
            expected_outputs=step_config.get('expected_outputs', []),
            timeout_seconds=step_config.get('timeout', 300),
            max_retries=step_config.get('max_retries', 2)
        )
    
    return builder


# Recovery utilities
def resume_failed_operations(task_id: str = None) -> List[str]:
    """Resume all failed operations for a task."""
    manager = micro_checkpoint_manager
    if task_id:
        manager.task_id = task_id
    
    recoverable_ops = manager.list_recoverable_operations()
    resumed_ops = []
    
    for op_info in recoverable_ops:
        operation_id = op_info["operation_id"]
        progress = manager.resume_operation(operation_id)
        
        if progress:
            resumed_ops.append(operation_id)
            print(f"🔄 Resumed operation: {operation_id}")
        else:
            print(f"❌ Failed to resume operation: {operation_id}")
    
    return resumed_ops


def get_operation_recovery_report(task_id: str = None) -> Dict[str, Any]:
    """Get a detailed report of recoverable operations."""
    manager = micro_checkpoint_manager
    if task_id:
        manager.task_id = task_id
    
    recoverable_ops = manager.list_recoverable_operations()
    
    report = {
        "task_id": manager.task_id,
        "total_recoverable_operations": len(recoverable_ops),
        "operations": recoverable_ops,
        "recovery_recommendations": []
    }
    
    for op in recoverable_ops:
        if op["failed_steps"] > 0:
            report["recovery_recommendations"].append({
                "operation_id": op["operation_id"],
                "issue": f"{op['failed_steps']} failed steps",
                "action": "Review error logs and retry with --resume-operation"
            })
        elif int(op["progress"].split("/")[0]) > 0:
            report["recovery_recommendations"].append({
                "operation_id": op["operation_id"], 
                "issue": "Partially completed",
                "action": "Resume from last checkpoint"
            })
    
    return report


# CLI integration
def print_recovery_status(task_id: str = None):
    """Print recovery status for human review."""
    report = get_operation_recovery_report(task_id)
    
    print(f"\n🔍 OPERATION RECOVERY STATUS")
    print(f"Task ID: {report['task_id']}")
    print(f"Recoverable Operations: {report['total_recoverable_operations']}")
    print("=" * 50)
    
    if not report["operations"]:
        print("✅ No operations need recovery")
        return
    
    for op in report["operations"]:
        print(f"\n📋 Operation: {op['operation_id']}")
        print(f"   Agent: {op['agent_name']}")
        print(f"   Progress: {op['progress']}")
        print(f"   Failed Steps: {op['failed_steps']}")
        print(f"   Created: {op['created_at']}")
        if op['current_step']:
            print(f"   Current Step: {op['current_step']}")
    
    if report["recovery_recommendations"]:
        print(f"\n🛠️  RECOVERY RECOMMENDATIONS:")
        for rec in report["recovery_recommendations"]:
            print(f"   • {rec['operation_id']}: {rec['issue']} → {rec['action']}")


import time  # Add missing import