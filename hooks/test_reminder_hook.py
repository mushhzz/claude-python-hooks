#!/usr/bin/env python3
"""
Post-tool-use hook to remind about running tests after code changes.

Tracks implementation file changes and reminds to run corresponding tests.
"""

import json
import sys
import os
from pathlib import Path


def find_test_file(file_path: str):
    """Find the corresponding test file for an implementation file."""
    path = Path(file_path)
    
    # Skip if already a test file
    if "test_" in path.name or "_test.py" in path.name:
        return None
    
    # Look for test file in tests subdirectory
    test_dir = path.parent / "tests"
    test_file = test_dir / f"test_{path.name}"
    
    if test_file.exists():
        return str(test_file)
    
    # Look for test file in parent tests directory
    test_dir = path.parent.parent / "tests"
    test_file = test_dir / f"test_{path.name}"
    
    if test_file.exists():
        return str(test_file)
    
    return None


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
    
    # Only check Python implementation files
    if not file_path.endswith(".py"):
        print(json.dumps({"decision": "approve"}))
        return 0
    
    # Skip test files and __init__ files
    if "test_" in os.path.basename(file_path) or "__init__.py" in file_path:
        print(json.dumps({"decision": "approve"}))
        return 0
    
    # Check if this is a significant change
    if tool_name == "Edit":
        old_string = tool_input.get("old_string", "")
        new_string = tool_input.get("new_string", "")
        
        # Skip minor changes (comments, docstrings, etc.)
        if len(old_string) < 50 and len(new_string) < 50:
            print(json.dumps({"decision": "approve"}))
            return 0
    
    # Find corresponding test file
    test_file = find_test_file(file_path)
    
    if test_file:
        print(json.dumps({
            "decision": "approve",
            "reason": (
                f"🧪 TEST REMINDER for {os.path.basename(file_path)}!\n\n"
                f"Test file found: {test_file}\n\n"
                "Per CLAUDE.md (TDD practices), run tests:\n"
                f"  uv run pytest {test_file} -v\n\n"
                "Or run all tests:\n"
                "  uv run pytest\n\n"
                "Ensure all tests pass after your changes!"
            )
        }))
    else:
        # No test file found - remind to create one
        path = Path(file_path)
        suggested_test_path = path.parent / "tests" / f"test_{path.name}"
        
        print(json.dumps({
            "decision": "approve",
            "reason": (
                f"⚠️ NO TESTS FOUND for {os.path.basename(file_path)}!\n\n"
                "Per CLAUDE.md (TDD requirement):\n"
                f"1. Create test file: {suggested_test_path}\n"
                "2. Write tests for your implementation\n"
                "3. Run: uv run pytest\n\n"
                "Remember: No feature is complete without tests!"
            )
        }))
    
    return 0


if __name__ == "__main__":
    sys.exit(main())