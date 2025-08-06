"""
Workflow error detection and handling system.

This module provides mechanisms for agents to signal critical workflow errors
that should stop the pipeline immediately.
"""

import re
from typing import Optional, List, Tuple
from enum import Enum


class WorkflowErrorLevel(Enum):
    """Error severity levels for workflow issues."""
    WARNING = "warning"      # Issue noted but can continue
    ERROR = "error"          # Significant problem but may be recoverable
    CRITICAL = "critical"    # Must stop immediately
    FATAL = "fatal"          # Unrecoverable system failure


class WorkflowError(Exception):
    """Exception raised when a critical workflow error is detected."""
    
    def __init__(self, message: str, level: WorkflowErrorLevel = WorkflowErrorLevel.CRITICAL, 
                 agent_name: str = None, context: dict = None):
        self.message = message
        self.level = level
        self.agent_name = agent_name
        self.context = context or {}
        super().__init__(self.format_error())
    
    def format_error(self) -> str:
        """Format the error message with context."""
        agent_info = f"[{self.agent_name}] " if self.agent_name else ""
        return f"🚨 WORKFLOW {self.level.value.upper()}: {agent_info}{self.message}"


# Define error markers that agents can use in their output
WORKFLOW_ERROR_MARKERS = {
    "CRITICAL_WORKFLOW_ERROR": WorkflowErrorLevel.CRITICAL,
    "FATAL_WORKFLOW_ERROR": WorkflowErrorLevel.FATAL,
    "WORKFLOW_ERROR": WorkflowErrorLevel.ERROR,
    "WORKFLOW_WARNING": WorkflowErrorLevel.WARNING,
}

# Regex patterns to detect error markers in agent output
ERROR_PATTERNS = [
    (r"🚨\s*CRITICAL_WORKFLOW_ERROR:\s*(.+)", WorkflowErrorLevel.CRITICAL),
    (r"💀\s*FATAL_WORKFLOW_ERROR:\s*(.+)", WorkflowErrorLevel.FATAL),
    (r"❌\s*WORKFLOW_ERROR:\s*(.+)", WorkflowErrorLevel.ERROR),
    (r"⚠️\s*WORKFLOW_WARNING:\s*(.+)", WorkflowErrorLevel.WARNING),
    # Additional patterns without emojis
    (r"CRITICAL_WORKFLOW_ERROR:\s*(.+)", WorkflowErrorLevel.CRITICAL),
    (r"FATAL_WORKFLOW_ERROR:\s*(.+)", WorkflowErrorLevel.FATAL),
    (r"WORKFLOW_ERROR:\s*(.+)", WorkflowErrorLevel.ERROR),
    (r"WORKFLOW_WARNING:\s*(.+)", WorkflowErrorLevel.WARNING),
]


def detect_workflow_errors(text: str, agent_name: str = None) -> List[Tuple[WorkflowErrorLevel, str]]:
    """
    Scan text for workflow error markers and return detected errors.
    
    Args:
        text: The text to scan (typically agent output)
        agent_name: Name of the agent that produced the text
    
    Returns:
        List of (error_level, error_message) tuples
    """
    errors = []
    
    for pattern, level in ERROR_PATTERNS:
        matches = re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE)
        for match in matches:
            error_message = match.group(1).strip()
            errors.append((level, error_message))
    
    return errors


def check_for_critical_errors(text: str, agent_name: str = None, 
                             stop_on_critical: bool = True) -> Optional[WorkflowError]:
    """
    Check text for critical workflow errors and optionally raise exception.
    
    Args:
        text: The text to check
        agent_name: Name of the agent that produced the text
        stop_on_critical: If True, raise WorkflowError on critical/fatal errors
    
    Returns:
        WorkflowError if critical error found and stop_on_critical is False
        None if no critical errors
    
    Raises:
        WorkflowError: If critical error found and stop_on_critical is True
    """
    errors = detect_workflow_errors(text, agent_name)
    
    # Find the most severe error
    critical_error = None
    for level, message in errors:
        if level in [WorkflowErrorLevel.CRITICAL, WorkflowErrorLevel.FATAL]:
            critical_error = WorkflowError(
                message=message,
                level=level,
                agent_name=agent_name
            )
            break
    
    if critical_error and stop_on_critical:
        raise critical_error
    
    return critical_error


def format_error_instructions() -> str:
    """
    Generate instructions for agents on how to signal workflow errors.
    
    Returns:
        Formatted string with error signaling instructions
    """
    return """
### WORKFLOW ERROR SIGNALING ###
If you detect a CRITICAL issue that should stop the entire workflow, use one of these markers:

1. **🚨 CRITICAL_WORKFLOW_ERROR:** [description] - For issues that make continuing impossible
   Example: 🚨 CRITICAL_WORKFLOW_ERROR: Missing required configuration file - cannot proceed

2. **💀 FATAL_WORKFLOW_ERROR:** [description] - For unrecoverable system failures
   Example: 💀 FATAL_WORKFLOW_ERROR: Database connection failed after 10 retries

3. **❌ WORKFLOW_ERROR:** [description] - For significant problems that may be recoverable
   Example: ❌ WORKFLOW_ERROR: Invalid data format in input file

4. **⚠️ WORKFLOW_WARNING:** [description] - For issues to note but can continue
   Example: ⚠️ WORKFLOW_WARNING: Using default values for missing parameters

IMPORTANT: Only use CRITICAL or FATAL errors when the workflow truly cannot continue.
The pipeline will stop immediately when these are detected.
"""


class WorkflowErrorHandler:
    """Handler for managing workflow errors across the pipeline."""
    
    def __init__(self, stop_on_critical: bool = True):
        self.stop_on_critical = stop_on_critical
        self.errors: List[WorkflowError] = []
        self.warnings: List[Tuple[str, str]] = []
    
    def check_agent_output(self, output: str, agent_name: str) -> bool:
        """
        Check agent output for workflow errors.
        
        Args:
            output: The agent's output text
            agent_name: Name of the agent
        
        Returns:
            True if workflow can continue, False if critical error found
        
        Raises:
            WorkflowError: If critical error and stop_on_critical is True
        """
        errors = detect_workflow_errors(output, agent_name)
        
        for level, message in errors:
            if level == WorkflowErrorLevel.WARNING:
                self.warnings.append((agent_name, message))
                print(f"⚠️ Workflow Warning from {agent_name}: {message}")
            elif level in [WorkflowErrorLevel.CRITICAL, WorkflowErrorLevel.FATAL]:
                error = WorkflowError(message, level, agent_name)
                self.errors.append(error)
                
                if self.stop_on_critical:
                    print(f"\n{'='*60}")
                    print(f"🚨 WORKFLOW STOPPED - CRITICAL ERROR DETECTED")
                    print(f"{'='*60}")
                    print(f"Agent: {agent_name}")
                    print(f"Level: {level.value.upper()}")
                    print(f"Error: {message}")
                    print(f"{'='*60}\n")
                    raise error
                return False
            else:
                # Regular error
                self.errors.append(WorkflowError(message, level, agent_name))
                print(f"❌ Workflow Error from {agent_name}: {message}")
        
        return True
    
    def get_summary(self) -> str:
        """Get a summary of all errors and warnings."""
        lines = []
        
        if self.errors:
            lines.append("=== WORKFLOW ERRORS ===")
            for error in self.errors:
                lines.append(f"  [{error.agent_name}] {error.level.value}: {error.message}")
        
        if self.warnings:
            lines.append("\n=== WORKFLOW WARNINGS ===")
            for agent, message in self.warnings:
                lines.append(f"  [{agent}] {message}")
        
        return "\n".join(lines) if lines else "No workflow issues detected"