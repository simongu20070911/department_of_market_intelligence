# /department_of_market_intelligence/utils/agent_context_preloader.py
"""
Agent-specific context pre-loading system.
Automatically loads required files for each agent type to eliminate manual file discovery.
"""

import os
import glob
from typing import Dict, Any, List, Optional, Tuple
from .. import config


class AgentContextPreloader:
    """Pre-loads context files for specific agent types to eliminate manual file discovery."""
    
    # Agent-specific context loading maps
    # Each agent gets exactly the files they need pre-loaded as template variables
    AGENT_CONTEXT_MAPS = {
        # Chief Researcher: Full context from previous work but retains tools for exploration
        "Chief_Researcher": {
            "task_description": "auto_load:{task_file_path}",
            "previous_critiques": "auto_load_directory:{outputs_dir}/planning/critiques/",
            "existing_plans": "auto_load_latest:{outputs_dir}/planning/research_plan_v*.md"
        },
        
        # Junior Validator: Fully pre-loaded (validation-focused, no exploration needed)
        "Junior_Validator": {
            "artifact_content": "auto_load:{artifact_to_validate}",
            "research_plan": "auto_load:{plan_artifact_name}",
        },
        
        # Senior Validator: Fully pre-loaded (validation-focused, no exploration needed)
        "Senior_Validator": {
            "artifact_content": "auto_load:{artifact_to_validate}",
            "junior_critique": "auto_load_latest:{outputs_dir}/planning/critiques/junior_critique_v*.md",
            "research_plan": "auto_load:{plan_artifact_name}",
            "previous_senior_critiques": "auto_load_directory:{outputs_dir}/planning/critiques/senior_*"
        },
        
        # Orchestrator: Full context for planning but retains tools for environment exploration
        "Orchestrator": {
            "research_plan": "auto_load:{plan_artifact_name}",
            "task_description": "auto_load:{task_file_path}",
            "validation_feedback": "auto_load_latest:{outputs_dir}/planning/critiques/*_critique_v*.md"
        },
        
        # Experiment Executor: Fully pre-loaded (execution-focused)
        "Experiment_Executor": {
            "implementation_manifest": "auto_load:{implementation_manifest_artifact}",
            "code_files": "auto_load_directory:{outputs_dir}/workspace/scripts/",
            "previous_execution_logs": "auto_load_latest:{outputs_dir}/execution_*.md"
        },
        
        # Coder Agent: Fully pre-loaded (implementation-focused)
        "Coder_Agent": {
            "implementation_manifest": "auto_load:{implementation_manifest_artifact}",
            "task_description": "auto_load:{task_file_path}",
            "validation_feedback": "auto_load_latest:{outputs_dir}/planning/critiques/*_critique_v*.md"
        }
    }
    
    # Content size limits to prevent context overflow
    MAX_FILE_SIZE_CHARS = 50000  # ~12-15k tokens for large files
    MAX_TOTAL_CONTEXT_CHARS = 200000  # ~50k tokens total context
    DIRECTORY_MAX_FILES = 10  # Max files to load from directory patterns
    
    @classmethod
    def preload_context_for_agent(cls, agent_name: str, session_state: Dict[str, Any]) -> Dict[str, str]:
        """
        Pre-load all required context files for a specific agent.
        
        Args:
            agent_name: Name of the agent (e.g., "Chief_Researcher", "Junior_Validator")
            session_state: Current session state with file paths and variables
            
        Returns:
            Dictionary of {template_variable: file_content} for injection
        """
        if agent_name not in cls.AGENT_CONTEXT_MAPS:
            return {}
        
        context_map = cls.AGENT_CONTEXT_MAPS[agent_name]
        preloaded_context = {}
        total_chars = 0
        
        print(f"\n📁 Pre-loading context for {agent_name}...")
        
        for template_var, load_instruction in context_map.items():
            try:
                # Resolve template variables in the load instruction
                resolved_instruction = cls._resolve_template_variables(load_instruction, session_state)
                
                # Load content based on instruction type
                content = cls._execute_load_instruction(resolved_instruction)
                
                if content:
                    # Truncate if too large
                    if len(content) > cls.MAX_FILE_SIZE_CHARS:
                        content = cls._truncate_content(content, template_var)
                    
                    preloaded_context[template_var] = content
                    total_chars += len(content)
                    
                    print(f"   ✅ {template_var}: {len(content)} chars loaded")
                    
                    # Check total context size
                    if total_chars > cls.MAX_TOTAL_CONTEXT_CHARS:
                        print(f"   ⚠️  Total context size limit reached ({total_chars} chars)")
                        break
                else:
                    print(f"   ⚠️  {template_var}: No content found")
                    
            except Exception as e:
                print(f"   ❌ {template_var}: Error loading - {str(e)}")
                # Continue with other context items even if one fails
                continue
        
        print(f"📊 Total context pre-loaded: {total_chars} chars ({len(preloaded_context)} items)")
        return preloaded_context
    
    @classmethod
    def _resolve_template_variables(cls, instruction: str, session_state: Dict[str, Any]) -> str:
        """Resolve template variables in load instructions using session state."""
        from datetime import datetime
        
        # Get variables from session state and config
        task_id = session_state.get("task_id") or config.TASK_ID
        outputs_dir = config.get_outputs_dir(task_id)
        
        # Build replacement map
        replacements = {
            "{task_file_path}": session_state.get("task_file_path", f"{config.TASKS_DIR}/{task_id}.md"),
            "{outputs_dir}": outputs_dir,
            "{artifact_to_validate}": session_state.get("artifact_to_validate", ""),
            "{plan_artifact_name}": session_state.get("plan_artifact_name", ""),
            "{implementation_manifest_artifact}": session_state.get("implementation_manifest_artifact", ""),
            "{task_id}": task_id,
            "{validation_version}": str(session_state.get("validation_version", 0)),
        }
        
        # Apply replacements
        result = instruction
        for placeholder, value in replacements.items():
            if placeholder in result and value:
                result = result.replace(placeholder, str(value))
        
        return result
    
    @classmethod
    def _execute_load_instruction(cls, instruction: str) -> str:
        """Execute a load instruction and return content."""
        if instruction.startswith("auto_load:"):
            file_path = instruction[10:]  # Remove "auto_load:" prefix
            return cls._load_single_file(file_path)
        
        elif instruction.startswith("auto_load_directory:"):
            dir_pattern = instruction[20:]  # Remove "auto_load_directory:" prefix
            return cls._load_directory(dir_pattern)
        
        elif instruction.startswith("auto_load_latest:"):
            file_pattern = instruction[17:]  # Remove "auto_load_latest:" prefix
            return cls._load_latest_file(file_pattern)
        
        else:
            return ""
    
    @classmethod
    def _load_single_file(cls, file_path: str) -> str:
        """Load content from a single file."""
        if not file_path or not os.path.exists(file_path):
            return ""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            return content if content else ""
        except Exception:
            return ""
    
    @classmethod
    def _load_directory(cls, dir_pattern: str) -> str:
        """Load and combine content from all files matching directory pattern."""
        if not dir_pattern:
            return ""
        
        # Handle both directory paths and glob patterns
        if dir_pattern.endswith('/'):
            # Directory path - list all files
            if os.path.isdir(dir_pattern):
                files = [os.path.join(dir_pattern, f) for f in os.listdir(dir_pattern) 
                        if os.path.isfile(os.path.join(dir_pattern, f))]
            else:
                return ""
        else:
            # Glob pattern
            files = glob.glob(dir_pattern)
        
        if not files:
            return ""
        
        # Sort by modification time (newest first) and limit count
        files = sorted(files, key=lambda x: os.path.getmtime(x) if os.path.exists(x) else 0, reverse=True)
        files = files[:cls.DIRECTORY_MAX_FILES]
        
        combined_content = []
        for file_path in files:
            content = cls._load_single_file(file_path)
            if content:
                filename = os.path.basename(file_path)
                combined_content.append(f"### {filename} ###\n{content}")
        
        return "\n\n".join(combined_content)
    
    @classmethod
    def _load_latest_file(cls, file_pattern: str) -> str:
        """Load content from the most recent file matching the pattern."""
        if not file_pattern:
            return ""
        
        files = glob.glob(file_pattern)
        if not files:
            return ""
        
        # Get the most recent file by modification time
        latest_file = max(files, key=lambda x: os.path.getmtime(x) if os.path.exists(x) else 0)
        return cls._load_single_file(latest_file)
    
    @classmethod
    def _truncate_content(cls, content: str, context_name: str) -> str:
        """Truncate content intelligently while preserving structure."""
        if len(content) <= cls.MAX_FILE_SIZE_CHARS:
            return content
        
        # For structured content, try to keep beginning and end
        lines = content.split('\n')
        if len(lines) > 20:
            # Keep first 60% and last 20% of lines with truncation notice
            keep_start = int(len(lines) * 0.6)
            keep_end = int(len(lines) * 0.2)
            
            truncated_lines = (
                lines[:keep_start] +
                [f"\n... [TRUNCATED: {len(lines) - keep_start - keep_end} lines omitted for {context_name}] ...\n"] +
                lines[-keep_end:]
            )
            return '\n'.join(truncated_lines)
        else:
            # Simple character truncation for short files
            truncate_point = cls.MAX_FILE_SIZE_CHARS - 200
            return content[:truncate_point] + f"\n\n... [TRUNCATED: Content too large for {context_name}] ..."
    
    @classmethod
    def get_context_summary(cls, agent_name: str, preloaded_context: Dict[str, str]) -> str:
        """Generate a summary of what context was loaded for debugging."""
        if not preloaded_context:
            return f"No context pre-loaded for {agent_name}"
        
        summary_lines = [f"📁 Context loaded for {agent_name}:"]
        total_chars = 0
        
        for template_var, content in preloaded_context.items():
            char_count = len(content)
            total_chars += char_count
            
            # Count lines and detect content type
            line_count = content.count('\n') + 1 if content else 0
            
            if "###" in content:
                # Multiple files combined
                file_count = content.count("###")
                summary_lines.append(f"   • {template_var}: {file_count} files, {char_count} chars, {line_count} lines")
            else:
                # Single file
                summary_lines.append(f"   • {template_var}: {char_count} chars, {line_count} lines")
        
        summary_lines.append(f"📊 Total: {total_chars} chars")
        return "\n".join(summary_lines)


# Convenience functions for easy integration

def preload_context_for_agent(agent_name: str, session_state: Dict[str, Any]) -> Dict[str, str]:
    """Convenience function to pre-load context for an agent."""
    return AgentContextPreloader.preload_context_for_agent(agent_name, session_state)


def get_supported_agents() -> List[str]:
    """Get list of agents that support context pre-loading."""
    return list(AgentContextPreloader.AGENT_CONTEXT_MAPS.keys())


def is_agent_supported(agent_name: str) -> bool:
    """Check if an agent supports context pre-loading."""
    return agent_name in AgentContextPreloader.AGENT_CONTEXT_MAPS