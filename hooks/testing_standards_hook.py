#!/usr/bin/env python3
"""
Hook to enforce testing standards per CLAUDE.md.

Enforces:
- Test files must be in tests/ subdirectories next to code
- Test-driven development practices
- Proper test naming conventions
- Coverage requirements
"""

import json
import sys
import re
import os
from pathlib import Path


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
    
    # Check for test file creation in wrong location
    if tool_name in ["Write", "Edit", "MultiEdit"]:
        file_path = tool_input.get("file_path", "")
        
        # Check if it's a test file
        if "test_" in os.path.basename(file_path) or "_test.py" in file_path:
            path_obj = Path(file_path)
            
            # Check if test is in a tests/ subdirectory
            if "tests" not in path_obj.parts:
                print(json.dumps({
                    "decision": "block",
                    "reason": (
                        "Test files must be in 'tests/' subdirectories! Per CLAUDE.md:\n"
                        "Vertical slice architecture requires tests next to code:\n\n"
                        "Example structure:\n"
                        "  features/user_management/\n"
                        "    handlers.py\n"
                        "    tests/\n"
                        "      test_handlers.py\n\n"
                        "Move this test to the appropriate tests/ subdirectory."
                    )
                }))
                return 1
            
            # Check test naming convention
            filename = os.path.basename(file_path)
            if not filename.startswith("test_"):
                print(json.dumps({
                    "decision": "block",
                    "reason": (
                        "Test files must start with 'test_'! Per CLAUDE.md:\n"
                        "Proper naming: test_module.py, test_feature.py\n"
                        f"Rename '{filename}' to start with 'test_'"
                    )
                }))
                return 1
        
        # Check for implementation without tests
        if tool_name == "Write" and file_path.endswith(".py"):
            if "test" not in file_path and "tests" not in file_path:
                # This is a new implementation file
                content = tool_input.get("content", "")
                
                # Check if it contains functions or classes
                if re.search(r'^\s*(def|class)\s+\w+', content, re.MULTILINE):
                    # Look for corresponding test file
                    path_obj = Path(file_path)
                    test_dir = path_obj.parent / "tests"
                    test_file = test_dir / f"test_{path_obj.name}"
                    
                    print(json.dumps({
                        "decision": "approve",
                        "reason": (
                            "REMINDER: Follow TDD! Per CLAUDE.md:\n"
                            f"Create test file: {test_file}\n"
                            "Write tests BEFORE implementation."
                        )
                    }))
                    return 0
    
    # Check Bash commands for testing
    elif tool_name == "Bash":
        command = tool_input.get("command", "")
        
        # Check for pytest execution (but not in strings like PR titles)
        # Only match pytest as a command, not within quoted strings
        if re.match(r'^pytest\s', command) or re.search(r'[;&|]\s*pytest\s', command):
            # Ensure using uv run or venv_linux
            if not command.startswith("uv run") and "venv_linux" not in command:
                print(json.dumps({
                    "decision": "block",
                    "reason": (
                        "Run pytest with UV! Per CLAUDE.md:\n"
                        "  uv run pytest\n"
                        "  uv run pytest tests/test_module.py -v\n"
                        "  uv run pytest --cov=src --cov-report=html"
                    )
                }))
                return 1
            
            # Suggest coverage for general pytest runs
            if not re.search(r'--cov', command) and not re.search(r'test_\w+\.py', command):
                print(json.dumps({
                    "decision": "approve",
                    "reason": (
                        "TIP: Run with coverage! Per CLAUDE.md:\n"
                        "  uv run pytest --cov=src --cov-report=html\n"
                        "Aim for 80%+ coverage on critical paths."
                    )
                }))
                return 0
        
        # Check for unittest (suggest pytest)
        if re.search(r'python.*-m\s+unittest', command):
            print(json.dumps({
                "decision": "block",
                "reason": (
                    "Use pytest instead of unittest! Per CLAUDE.md:\n"
                    "pytest is the standard testing framework.\n"
                    "  uv run pytest\n"
                    "  uv run pytest tests/ -v"
                )
            }))
            return 1
    
    # Approve by default
    print(json.dumps({"decision": "approve"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())