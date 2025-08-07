# /department_of_market_intelligence/tools/json_fixer.py
"""Smart JSON parser that can fix common LLM-generated JSON issues."""

import json
import re
from typing import Any, Dict, List, Optional, Tuple


def fix_llm_json(content: str) -> Tuple[bool, Optional[Dict], str]:
    """
    Attempt to fix and parse JSON that may contain JavaScript-like syntax.
    
    Returns:
        (success, parsed_data, error_or_fixed_json)
        - If successful: (True, parsed_dict, fixed_json_string)
        - If failed: (False, None, error_message)
    """
    
    # First, try to parse as-is
    try:
        parsed = json.loads(content)
        return True, parsed, content
    except json.JSONDecodeError:
        pass  # Continue with fixes
    
    # Create a working copy
    fixed_content = content
    
    # Fix 1: Remove JavaScript comments
    fixed_content = re.sub(r'//.*?$', '', fixed_content, flags=re.MULTILINE)
    fixed_content = re.sub(r'/\*.*?\*/', '', fixed_content, flags=re.DOTALL)
    
    # Fix 2: Replace template literals (backticks) with double quotes
    # But be careful not to break multi-line strings
    def replace_template_literal(match):
        inner = match.group(1)
        # Replace ${} interpolations with placeholders
        inner = re.sub(r'\$\{([^}]+)\}', r'_\1_', inner)
        return f'"{inner}"'
    
    fixed_content = re.sub(r'`([^`]*)`', replace_template_literal, fixed_content)
    
    # Fix 3: Convert single quotes to double quotes (carefully)
    # Only if they're used as string delimiters, not inside strings
    def smart_quote_replace(text):
        result = []
        in_string = False
        string_char = None
        i = 0
        while i < len(text):
            if not in_string:
                if text[i] == '"':
                    in_string = True
                    string_char = '"'
                    result.append(text[i])
                elif text[i] == "'":
                    # Check if this is a string delimiter
                    # Look ahead to find the closing quote
                    j = i + 1
                    while j < len(text) and text[j] != "'":
                        if text[j] == '\\' and j + 1 < len(text):
                            j += 2  # Skip escaped character
                        else:
                            j += 1
                    if j < len(text):
                        # Found closing quote, replace both with double quotes
                        result.append('"')
                        result.append(text[i+1:j])
                        result.append('"')
                        i = j
                    else:
                        result.append(text[i])
                else:
                    result.append(text[i])
            else:
                if text[i] == string_char and (i == 0 or text[i-1] != '\\'):
                    in_string = False
                    string_char = None
                result.append(text[i])
            i += 1
        return ''.join(result)
    
    fixed_content = smart_quote_replace(fixed_content)
    
    # Fix 4: Handle spread operators and Array.from
    # Look for patterns like ...Array.from({ length: 10 }, (_, i) => ({...}))
    
    # First, let's detect if there's a spread operator with Array.from
    array_from_pattern = r'\.\.\.Array\.from\(\{[^}]+\},\s*\([^)]+\)\s*=>\s*\([^)]+\)\)'
    
    if re.search(array_from_pattern, fixed_content):
        # This is complex - we need to expand it
        # For now, let's try a simpler approach: look for the pattern and try to understand it
        
        # Extract the task array if it exists
        task_match = re.search(r'"tasks"\s*:\s*\[(.*?)\]', fixed_content, re.DOTALL)
        if task_match:
            tasks_content = task_match.group(1)
            
            # Look for the spread operator pattern
            spread_match = re.search(
                r'\.\.\.Array\.from\(\{\s*length:\s*(\d+)\s*\},\s*\([^,]+,\s*([^)]+)\)\s*=>\s*\((\{[^}]+\})\)\)',
                tasks_content,
                re.DOTALL
            )
            
            if spread_match:
                count = int(spread_match.group(1))
                index_var = spread_match.group(2).strip()
                template = spread_match.group(3)
                
                # Generate the expanded tasks
                expanded_tasks = []
                
                # First, add any tasks before the spread operator
                before_spread = tasks_content[:tasks_content.find('...Array.from')]
                
                # Parse any existing tasks
                existing_tasks = []
                try:
                    # Try to extract complete task objects before the spread
                    task_obj_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
                    existing_matches = re.findall(task_obj_pattern, before_spread)
                    for match in existing_matches:
                        try:
                            # Clean up and parse
                            cleaned = match.strip()
                            if cleaned.endswith(','):
                                cleaned = cleaned[:-1]
                            task = json.loads(cleaned)
                            existing_tasks.append(task)
                        except:
                            pass
                except:
                    pass
                
                # Now expand the template for each index
                for i in range(count):
                    # Replace ${i} or similar patterns with actual values
                    expanded = template
                    expanded = expanded.replace(f'${{{index_var} + 1}}', str(i + 1))
                    expanded = expanded.replace(f'${{{index_var}}}', str(i))
                    expanded = expanded.replace(f'$({index_var} + 1)', str(i + 1))
                    expanded = expanded.replace(f'$({index_var})', str(i))
                    
                    # Also handle template literals that might use the index
                    expanded = re.sub(r'\$\{[^}]*' + index_var + r'[^}]*\}', str(i + 1), expanded)
                    
                    try:
                        task = json.loads(expanded)
                        expanded_tasks.append(task)
                    except:
                        # If individual parsing fails, skip this one
                        pass
                
                # Add any tasks after the spread operator
                after_pattern = r'\)\)\s*,(.*)$'
                after_match = re.search(after_pattern, tasks_content, re.DOTALL)
                if after_match:
                    after_content = after_match.group(1)
                    # Try to parse remaining tasks
                    remaining_matches = re.findall(task_obj_pattern, after_content)
                    for match in remaining_matches:
                        try:
                            cleaned = match.strip()
                            if cleaned.endswith(','):
                                cleaned = cleaned[:-1]
                            task = json.loads(cleaned)
                            expanded_tasks.append(task)
                        except:
                            pass
                
                # Now reconstruct the JSON with expanded tasks
                all_tasks = existing_tasks + expanded_tasks
                
                # Build the final JSON structure
                try:
                    # Extract other fields from the original content
                    result = {}
                    
                    # Get research_plan_artifact if it exists
                    plan_match = re.search(r'"research_plan_artifact"\s*:\s*"([^"]+)"', fixed_content)
                    if plan_match:
                        result['research_plan_artifact'] = plan_match.group(1)
                    
                    result['tasks'] = all_tasks
                    
                    return True, result, json.dumps(result, indent=2)
                except:
                    pass
    
    # Fix 5: Handle trailing commas
    # Remove trailing commas before } or ]
    fixed_content = re.sub(r',\s*}', '}', fixed_content)
    fixed_content = re.sub(r',\s*\]', ']', fixed_content)
    
    # Fix 6: Convert Python booleans to JSON booleans
    fixed_content = re.sub(r'\bTrue\b', 'true', fixed_content)
    fixed_content = re.sub(r'\bFalse\b', 'false', fixed_content)
    fixed_content = re.sub(r'\bNone\b', 'null', fixed_content)
    
    # Try to parse the fixed content
    try:
        parsed = json.loads(fixed_content)
        return True, parsed, fixed_content
    except json.JSONDecodeError as e:
        # If it still fails, try one more aggressive approach
        # Extract just the essential structure
        try:
            # Look for tasks array
            tasks = []
            task_pattern = r'\{\s*"task_id"\s*:\s*"[^"]+".+?\}'
            task_matches = re.finditer(task_pattern, fixed_content, re.DOTALL)
            
            for match in task_matches:
                try:
                    task_str = match.group(0)
                    # Clean up this individual task
                    task_str = re.sub(r',\s*}', '}', task_str)
                    task = json.loads(task_str)
                    tasks.append(task)
                except:
                    continue
            
            if tasks:
                # Build a minimal valid structure
                result = {
                    "research_plan_artifact": "",
                    "tasks": tasks
                }
                
                # Try to extract the research plan artifact
                plan_match = re.search(r'"research_plan_artifact"\s*:\s*"([^"]+)"', fixed_content)
                if plan_match:
                    result['research_plan_artifact'] = plan_match.group(1)
                
                return True, result, json.dumps(result, indent=2)
        except:
            pass
        
        return False, None, f"Failed to parse JSON: {str(e)}"


def load_implementation_manifest(file_path: str) -> Tuple[bool, Optional[Dict], str]:
    """
    Load and fix an implementation manifest file.
    
    Returns:
        (success, parsed_data, message)
    """
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        success, data, result = fix_llm_json(content)
        
        if success:
            # Validate the structure
            if not isinstance(data, dict):
                return False, None, "Manifest must be a JSON object"
            
            if 'tasks' not in data:
                return False, None, "Manifest missing 'tasks' field"
            
            if not isinstance(data['tasks'], list):
                return False, None, "'tasks' must be an array"
            
            # Validate each task has required fields
            for i, task in enumerate(data['tasks']):
                if not isinstance(task, dict):
                    return False, None, f"Task {i} is not an object"
                
                required = ['task_id', 'description', 'dependencies']
                for field in required:
                    if field not in task:
                        # Try to add sensible defaults
                        if field == 'dependencies':
                            task['dependencies'] = []
                        elif field == 'task_id':
                            task['task_id'] = f'task_{i:02d}'
                        elif field == 'description':
                            task['description'] = f'Task {i}'
            
            return True, data, "Successfully parsed and fixed manifest"
        else:
            return False, None, result
            
    except FileNotFoundError:
        return False, None, f"File not found: {file_path}"
    except Exception as e:
        return False, None, f"Error reading file: {str(e)}"


# Test the fixer with the problematic JSON
if __name__ == "__main__":
    test_json = '''
    {
        "research_plan_artifact": "/path/to/plan.md",
        "tasks": [
            {
                "task_id": "task_01",
                "description": "First task",
                "dependencies": []
            },
            ...Array.from({ length: 10 }, (_, i) => ({
                "task_id": `task_${i + 2}`,
                "description": `Task number ${i + 2}`,
                "dependencies": ["task_01"]
            }))
        ]
    }
    '''
    
    success, data, result = fix_llm_json(test_json)
    if success:
        print("Successfully fixed!")
        print(json.dumps(data, indent=2))
    else:
        print(f"Failed: {result}")