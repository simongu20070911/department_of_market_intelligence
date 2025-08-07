# /department_of_market_intelligence/tools/json_validator.py
"""JSON validation tool for validators to check manifest syntax."""

import json
from typing import Dict, Any
from google.adk.tools import FunctionTool


def validate_json_content(content: str) -> Dict[str, Any]:
    """
    Validate that a string contains valid JSON.
    This tool is specifically for validators to check JSON syntax.
    
    Args:
        content: JSON string content to validate
        
    Returns:
        A dictionary with validation results:
        - is_valid: Boolean indicating if JSON is valid
        - error: Error message if invalid, None if valid
        - has_javascript: Boolean indicating if JavaScript code was detected
        - javascript_indicators: List of JS code patterns found
        - parsed_data: The parsed JSON data if valid, None otherwise
    """
    # Check for JavaScript code patterns
    js_patterns = []
    if "..." in content and "Array" in content:
        js_patterns.append("Spread operator (...)")
    if "Array.from(" in content:
        js_patterns.append("Array.from() method")
    if "=>" in content:
        js_patterns.append("Arrow function (=>)")
    if "`" in content and "${" in content:
        js_patterns.append("Template literals with interpolation")
    elif "`" in content:
        js_patterns.append("Template literals (backticks)")
    if "//" in content or "/*" in content:
        # Check if it's actually in a string value
        try:
            # Quick parse to see if comments are in strings
            temp_parse = json.loads(content)
        except:
            js_patterns.append("JavaScript comments")
    
    # Try to parse as JSON
    try:
        parsed = json.loads(content)
        
        # Additional validation: check structure for implementation manifest
        validation_notes = []
        if isinstance(parsed, dict) and "tasks" in parsed:
            # This looks like an implementation manifest
            if not isinstance(parsed.get("tasks"), list):
                validation_notes.append("'tasks' should be an array")
            else:
                for i, task in enumerate(parsed["tasks"]):
                    if not isinstance(task, dict):
                        validation_notes.append(f"Task {i} is not an object")
                    else:
                        # Check required fields
                        required_fields = ["task_id", "description", "dependencies"]
                        for field in required_fields:
                            if field not in task:
                                validation_notes.append(f"Task {i} missing required field '{field}'")
        
        return {
            "is_valid": True,
            "error": None,
            "has_javascript": len(js_patterns) > 0,
            "javascript_indicators": js_patterns,
            "parsed_data": parsed,
            "validation_notes": validation_notes
        }
    except json.JSONDecodeError as e:
        return {
            "is_valid": False,
            "error": f"JSON parse error at line {e.lineno}, column {e.colno}: {e.msg}",
            "has_javascript": len(js_patterns) > 0,
            "javascript_indicators": js_patterns,
            "parsed_data": None,
            "validation_notes": []
        }
    except Exception as e:
        return {
            "is_valid": False,
            "error": f"Unexpected error: {str(e)}",
            "has_javascript": False,
            "javascript_indicators": [],
            "parsed_data": None,
            "validation_notes": []
        }


# Create the tool wrapper
json_validator_tool = FunctionTool(validate_json_content)