#!/usr/bin/env python3
"""
Hook to enforce Python file size and structure limits per CLAUDE.md.

Enforces:
- Files must be under 500 lines
- Functions must be under 50 lines
- Classes must be under 100 lines
"""

import json
import sys
import os
import ast
from pathlib import Path


def count_lines_in_string(content: str) -> int:
    """Count actual lines in content."""
    return len(content.splitlines())


def analyze_python_code(file_path: str, content: str) -> list:
    """Analyze Python code for violations of size limits."""
    violations = []
    
    try:
        tree = ast.parse(content)
    except SyntaxError:
        # If file has syntax errors, let it through for Claude to fix
        return violations
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            func_lines = node.end_lineno - node.lineno + 1
            if func_lines > 50:
                violations.append(
                    f"Function '{node.name}' at line {node.lineno} "
                    f"is {func_lines} lines (max 50)"
                )
        
        elif isinstance(node, ast.ClassDef):
            class_lines = node.end_lineno - node.lineno + 1
            if class_lines > 100:
                violations.append(
                    f"Class '{node.name}' at line {node.lineno} "
                    f"is {class_lines} lines (max 100)"
                )
    
    return violations


def main():
    # Read input from stdin
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(json.dumps({
            "decision": "approve",
            "reason": f"Failed to parse input: {e}"
        }))
        return 0
    
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    
    # Check for Write and Edit tools on Python files
    if tool_name in ["Write", "Edit", "MultiEdit"]:
        file_path = tool_input.get("file_path", "")
        
        # Only check Python files
        if not file_path.endswith(".py"):
            print(json.dumps({"decision": "approve"}))
            return 0
        
        # For Write tool, check content directly
        if tool_name == "Write":
            content = tool_input.get("content", "")
            line_count = count_lines_in_string(content)
            
            if line_count > 500:
                print(json.dumps({
                    "decision": "block",
                    "reason": (
                        f"File would be {line_count} lines (max 500). "
                        "Per CLAUDE.md: Split into multiple modules."
                    )
                }))
                return 1
            
            # Analyze code structure
            violations = analyze_python_code(file_path, content)
            if violations:
                print(json.dumps({
                    "decision": "block",
                    "reason": (
                        "Code structure violations per CLAUDE.md:\n" +
                        "\n".join(f"  - {v}" for v in violations)
                    )
                }))
                return 1
        
        # For Edit/MultiEdit, check if file would exceed limits after edit
        elif tool_name in ["Edit", "MultiEdit"]:
            # Try to read existing file to check post-edit size
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r') as f:
                        current_content = f.read()
                    
                    # Estimate new content (this is approximate)
                    if tool_name == "Edit":
                        new_string = tool_input.get("new_string", "")
                        new_lines = count_lines_in_string(new_string)
                        if new_lines > 50:
                            print(json.dumps({
                                "decision": "block",
                                "reason": (
                                    f"Edit adds {new_lines} lines. "
                                    "Consider breaking into smaller edits or refactoring."
                                )
                            }))
                            return 1
                except Exception:
                    pass  # If we can't read, let it through
    
    # Check for Read tool on Python files
    elif tool_name == "Read":
        file_path = tool_input.get("file_path", "")
        
        if file_path.endswith(".py") and os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    line_count = sum(1 for _ in f)
                
                if line_count > 500:
                    print(json.dumps({
                        "decision": "approve",
                        "reason": (
                            f"WARNING: File has {line_count} lines (exceeds 500). "
                            "Per CLAUDE.md: This file should be refactored."
                        )
                    }))
                    return 0
            except Exception:
                pass
    
    # Approve by default
    print(json.dumps({"decision": "approve"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())