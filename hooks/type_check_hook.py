#!/usr/bin/env python3
"""
Post-tool-use hook to enforce type checking with mypy after Python file modifications.

Ensures type hints are properly used and validates type safety.
"""

import json
import sys
import os
import subprocess
from pathlib import Path


def check_mypy_installed():
    """Check if mypy is available in the project."""
    try:
        # Try uv run mypy first
        result = subprocess.run(
            ["uv", "run", "mypy", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return "uv"
    except:
        pass
    
    try:
        # Try mypy directly
        result = subprocess.run(
            ["mypy", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return "direct"
    except:
        pass
    
    return None


def check_has_type_hints(file_path: str):
    """Check if file has any function definitions that need type hints."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Look for function definitions without type hints
        import re
        
        # Find all function definitions
        func_pattern = r'^\s*def\s+(\w+)\s*\(([^)]*)\)\s*(?:->|:)'
        functions = re.findall(func_pattern, content, re.MULTILINE)
        
        if not functions:
            return True  # No functions to check
        
        # Check for functions without return type hints
        no_return_hint = re.findall(r'^\s*def\s+\w+\s*\([^)]*\)\s*:', content, re.MULTILINE)
        
        if no_return_hint:
            return False  # Found functions without return type hints
        
        return True
        
    except Exception:
        return True  # On error, don't block


def run_mypy_check(file_path: str, mypy_mode: str):
    """Run mypy on the file and return type errors."""
    if mypy_mode == "uv":
        cmd = ["uv", "run", "mypy", file_path, "--no-error-summary"]
    else:
        cmd = ["mypy", file_path, "--no-error-summary"]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            return None  # No type errors
        
        # Parse mypy output
        errors = []
        for line in result.stdout.split('\n'):
            if line and not line.startswith('Found'):
                errors.append(line)
        
        return errors[:10]  # Return first 10 errors
            
    except Exception as e:
        return None  # Don't block on error


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
    
    # Only check after Write/Edit/MultiEdit on Python files
    if tool_name not in ["Write", "Edit", "MultiEdit"]:
        print(json.dumps({"decision": "approve"}))
        return 0
    
    file_path = tool_input.get("file_path", "")
    
    # Only check Python files (skip __init__.py and test files)
    if not file_path.endswith(".py"):
        print(json.dumps({"decision": "approve"}))
        return 0
    
    if "__init__.py" in file_path or "test_" in os.path.basename(file_path):
        print(json.dumps({"decision": "approve"}))
        return 0
    
    # Check if file exists
    if not os.path.exists(file_path):
        print(json.dumps({"decision": "approve"}))
        return 0
    
    # Check for missing type hints
    if not check_has_type_hints(file_path):
        print(json.dumps({
            "decision": "approve",
            "reason": (
                "⚠️ MISSING TYPE HINTS! Per CLAUDE.md:\n"
                "Always use type hints for function signatures.\n\n"
                "Example:\n"
                "  def calculate(price: Decimal, tax: float) -> Decimal:\n"
                "      return price * Decimal(1 + tax)\n\n"
                "Add type hints to all functions!"
            )
        }))
        return 0
    
    # Check if mypy is available
    mypy_mode = check_mypy_installed()
    if not mypy_mode:
        # Don't remind about mypy if it's not installed - it's optional
        print(json.dumps({"decision": "approve"}))
        return 0
    
    # Run mypy check
    errors = run_mypy_check(file_path, mypy_mode)
    
    if errors is None or not errors:
        # No type errors
        print(json.dumps({"decision": "approve"}))
        return 0
    
    # Format error message
    error_text = "\n".join(f"  {e}" for e in errors)
    
    print(json.dumps({
        "decision": "approve",
        "reason": (
            f"⚠️ TYPE ERRORS DETECTED in {os.path.basename(file_path)}!\n\n"
            f"{error_text}\n\n"
            "Per CLAUDE.md, fix type errors:\n"
            f"  {'uv run ' if mypy_mode == 'uv' else ''}mypy {file_path}\n\n"
            "Ensure all type hints are correct!"
        )
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())