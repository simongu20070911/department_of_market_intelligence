# /department_of_market_intelligence/utils/state_adapter.py
"""
Adapter for migrating between dictionary-based state and Pydantic SessionState.
Provides compatibility layer during transition.
"""

from typing import Dict, Any, Optional
from .state_model import SessionState, TaskInfo, ValidationInfo, ExecutionInfo
import warnings


class StateAdapter:
    """Provides compatibility between dict state and SessionState model."""
    
    @staticmethod
    def dict_to_session_state(state_dict: Dict[str, Any], task_id: str) -> SessionState:
        """Convert legacy dictionary state to SessionState model.
        
        Args:
            state_dict: Legacy dictionary-based state
            task_id: Task ID for the session
            
        Returns:
            SessionState: Properly typed session state
        """
        # Create base session state
        session = SessionState(task_id=task_id)
        
        # Map simple fields
        field_mappings = {
            'current_date': 'current_date',
            'current_task': 'current_task',
            'plan_artifact_name': 'plan_artifact_name',
            'plan_version': 'plan_version',
            'implementation_manifest_artifact': 'implementation_manifest_artifact',
            'results_extraction_script_artifact': 'results_extraction_script_artifact',
            'artifact_to_validate': 'artifact_to_validate',
            'final_report_artifact': 'final_report_artifact',
            'final_results_artifact': 'final_results_artifact',
        }
        
        for old_key, new_key in field_mappings.items():
            if old_key in state_dict and state_dict[old_key] is not None:
                setattr(session, new_key, state_dict[old_key])
        
        # Map validation info
        if 'validation_version' in state_dict:
            session.validation_info.validation_version = state_dict['validation_version']
        if 'validation_status' in state_dict:
            session.validation_info.validation_status = state_dict['validation_status']
        if 'junior_critique_artifact' in state_dict:
            session.validation_info.junior_critique_artifact = state_dict['junior_critique_artifact']
        if 'senior_critique_artifact' in state_dict:
            session.validation_info.senior_critique_artifact = state_dict['senior_critique_artifact']
        if 'parallel_validation_critical_issues' in state_dict:
            session.validation_info.parallel_validation_critical_issues = state_dict['parallel_validation_critical_issues']
        if 'consolidated_validation_issues' in state_dict:
            session.validation_info.consolidated_validation_issues = state_dict['consolidated_validation_issues']
        
        # Map execution info
        if 'execution_status' in state_dict:
            session.execution_info.execution_status = state_dict['execution_status']
        if 'error_type' in state_dict:
            session.execution_info.error_type = state_dict['error_type']
        if 'error_details' in state_dict:
            session.execution_info.error_details = state_dict['error_details']
        if 'suggested_fix' in state_dict:
            session.execution_info.suggested_fix = state_dict['suggested_fix']
        
        # Map coder subtask
        if 'coder_subtask' in state_dict and isinstance(state_dict['coder_subtask'], dict):
            task_data = state_dict['coder_subtask']
            session.coder_subtask = TaskInfo(
                task_id=task_data.get('task_id', 'unknown'),
                description=task_data.get('description', ''),
                dependencies=task_data.get('dependencies', []),
                status=task_data.get('status', 'pending')
            )
        
        # Infer current phase from available data
        if state_dict.get('final_report_artifact'):
            session.current_phase = 'final_report'
        elif state_dict.get('results_extraction_script_artifact'):
            session.current_phase = 'results_extraction'
        elif state_dict.get('execution_status'):
            session.current_phase = 'execution'
        elif state_dict.get('implementation_manifest_artifact'):
            session.current_phase = 'implementation'
        else:
            session.current_phase = 'planning'
        
        # Store any unmapped fields in metadata (with size warning)
        unmapped_keys = set(state_dict.keys()) - set(field_mappings.keys()) - {
            'validation_version', 'validation_status', 'junior_critique_artifact',
            'senior_critique_artifact', 'execution_status', 'error_type', 
            'error_details', 'suggested_fix', 'coder_subtask',
            'parallel_validation_critical_issues', 'consolidated_validation_issues'
        }
        
        if unmapped_keys:
            warnings.warn(
                f"Unmapped state keys will be stored in metadata: {unmapped_keys}"
            )
            for key in unmapped_keys:
                value = state_dict[key]
                # Only store small values in metadata
                if isinstance(value, (str, int, float, bool)) or \
                   (isinstance(value, (list, dict)) and len(str(value)) < 1000):
                    session.metadata[key] = value
                else:
                    warnings.warn(
                        f"Skipping large value for key '{key}' - use file storage instead"
                    )
        
        return session
    
    @staticmethod
    def session_state_to_dict(session: SessionState) -> Dict[str, Any]:
        """Convert SessionState to dictionary for backward compatibility.
        
        Args:
            session: SessionState model instance
            
        Returns:
            Dict: Flattened dictionary matching legacy format
        """
        state_dict = {}
        
        # Map simple fields
        state_dict['task_id'] = session.task_id
        state_dict['current_date'] = session.current_date
        state_dict['current_task'] = session.current_task
        state_dict['plan_artifact_name'] = session.plan_artifact_name
        state_dict['plan_version'] = session.plan_version
        state_dict['implementation_manifest_artifact'] = session.implementation_manifest_artifact
        state_dict['results_extraction_script_artifact'] = session.results_extraction_script_artifact
        state_dict['artifact_to_validate'] = session.artifact_to_validate
        state_dict['final_report_artifact'] = session.final_report_artifact
        state_dict['final_results_artifact'] = session.final_results_artifact
        
        # Flatten validation info
        state_dict['validation_version'] = session.validation_info.validation_version
        state_dict['validation_status'] = session.validation_info.validation_status
        state_dict['junior_critique_artifact'] = session.validation_info.junior_critique_artifact
        state_dict['senior_critique_artifact'] = session.validation_info.senior_critique_artifact
        state_dict['parallel_validation_critical_issues'] = session.validation_info.parallel_validation_critical_issues
        state_dict['consolidated_validation_issues'] = session.validation_info.consolidated_validation_issues
        
        # Flatten execution info
        state_dict['execution_status'] = session.execution_info.execution_status
        state_dict['error_type'] = session.execution_info.error_type
        state_dict['error_details'] = session.execution_info.error_details
        state_dict['suggested_fix'] = session.execution_info.suggested_fix
        
        # Map coder subtask
        if session.coder_subtask:
            state_dict['coder_subtask'] = {
                'task_id': session.coder_subtask.task_id,
                'description': session.coder_subtask.description,
                'dependencies': session.coder_subtask.dependencies,
                'status': session.coder_subtask.status
            }
        
        # Add metadata
        state_dict.update(session.metadata)
        
        # Remove None values for cleaner output
        return {k: v for k, v in state_dict.items() if v is not None}
    
    @staticmethod
    def create_proxy_state(session: SessionState) -> 'StateProxy':
        """Create a proxy that provides dict-like access to SessionState.
        
        This allows gradual migration of agents without breaking existing code.
        """
        return StateProxy(session)


class StateProxy:
    """Provides dictionary-like interface to SessionState for compatibility."""
    
    def __init__(self, session: SessionState):
        self._session = session
        self._adapter = StateAdapter()
    
    def __getitem__(self, key: str) -> Any:
        """Get value using dictionary syntax."""
        # Type safety - ensure key is a string
        if not isinstance(key, str):
            raise TypeError(f"Key must be a string, got {type(key)}: {key}")
            
        # First check if it's a direct SessionState attribute
        if hasattr(self._session, key):
            return getattr(self._session, key)
        
        # Check flattened validation/execution fields
        if key == 'validation_status':
            return self._session.validation_info.validation_status
        elif key == 'validation_version':
            return self._session.validation_info.validation_version
        elif key == 'execution_status':
            return self._session.execution_info.execution_status
        elif key in ['junior_critique_artifact', 'senior_critique_artifact',
                     'parallel_validation_critical_issues', 'consolidated_validation_issues',
                     'error_type', 'error_details', 'suggested_fix']:
            # These are in nested objects
            if hasattr(self._session.validation_info, key):
                return getattr(self._session.validation_info, key)
            elif hasattr(self._session.execution_info, key):
                return getattr(self._session.execution_info, key)
        
        # Check metadata
        if key in self._session.metadata:
            return self._session.metadata[key]
        
        # Not found
        raise KeyError(f"Key '{key}' not found in session state")
    
    def __setitem__(self, key: str, value: Any) -> None:
        """Set value using dictionary syntax."""
        # Direct SessionState attributes
        if hasattr(self._session, key) and key != 'metadata':
            setattr(self._session, key, value)
            return
        
        # Special handling for nested fields
        if key == 'validation_status':
            self._session.validation_info.validation_status = value
        elif key == 'validation_version':
            self._session.validation_info.validation_version = value
        elif key == 'junior_critique_artifact':
            self._session.validation_info.junior_critique_artifact = value
        elif key == 'senior_critique_artifact':
            self._session.validation_info.senior_critique_artifact = value
        elif key == 'parallel_validation_critical_issues':
            self._session.validation_info.parallel_validation_critical_issues = value
        elif key == 'consolidated_validation_issues':
            self._session.validation_info.consolidated_validation_issues = value
        elif key == 'execution_status':
            self._session.execution_info.execution_status = value
        elif key == 'error_type':
            self._session.execution_info.error_type = value
        elif key == 'error_details':
            self._session.execution_info.error_details = value
        elif key == 'suggested_fix':
            self._session.execution_info.suggested_fix = value
        else:
            # Store in metadata as fallback
            self._session.metadata[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value with default."""
        try:
            return self[key]
        except KeyError:
            return default
    
    def __contains__(self, key: str) -> bool:
        """Check if key exists in state."""
        if not isinstance(key, str):
            return False
            
        try:
            self[key]
            return True
        except KeyError:
            return False
    
    def keys(self):
        """Return an iterator over keys."""
        # Return both direct attributes and metadata keys
        direct_keys = [attr for attr in dir(self._session) 
                      if not attr.startswith('_') and not callable(getattr(self._session, attr))]
        nested_keys = ['validation_status', 'validation_version', 'execution_status',
                      'junior_critique_artifact', 'senior_critique_artifact',
                      'parallel_validation_critical_issues', 'consolidated_validation_issues',
                      'error_type', 'error_details', 'suggested_fix']
        metadata_keys = list(self._session.metadata.keys())
        
        return iter(direct_keys + nested_keys + metadata_keys)
    
    def update(self, other: dict) -> None:
        """Update multiple values."""
        for key, value in other.items():
            self[key] = value