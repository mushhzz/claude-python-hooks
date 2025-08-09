#!/usr/bin/env python3
"""
Hook to enforce UV package management per CLAUDE.md.

Enforces:
- Never update dependencies directly in pyproject.toml
- Always use uv add/remove commands
- Use venv_linux for Python execution
"""

import json
import sys
import re


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
    
    # Check for direct edits to pyproject.toml
    if tool_name in ["Write", "Edit", "MultiEdit"]:
        file_path = tool_input.get("file_path", "")
        
        if file_path.endswith("pyproject.toml"):
            # Check if editing dependencies section
            if tool_name == "Write":
                content = tool_input.get("content", "")
            elif tool_name == "Edit":
                content = tool_input.get("new_string", "")
            else:  # MultiEdit
                edits = tool_input.get("edits", [])
                content = " ".join(e.get("new_string", "") for e in edits)
            
            # Look for dependency-related changes
            dep_patterns = [
                r'\[tool\.uv\.dependencies\]',
                r'\[project\.dependencies\]',
                r'\[tool\.uv\.dev-dependencies\]',
                r'dependencies\s*=\s*\[',
                r'requires\s*=\s*\[',
                r'"[^"]+==[\d\.]+"',  # Package version specs
                r'"[^"]+>=[\d\.]+"',
                r'"[^"]+~=[\d\.]+"',
            ]
            
            for pattern in dep_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    print(json.dumps({
                        "decision": "block",
                        "reason": (
                            "NEVER update dependencies directly in pyproject.toml! "
                            "Per CLAUDE.md: Always use UV commands:\n"
                            "  - Add package: uv add <package>\n"
                            "  - Add dev dependency: uv add --dev <package>\n"
                            "  - Remove package: uv remove <package>\n"
                            "  - Update all: uv sync"
                        )
                    }))
                    return 1
    
    # Check Bash commands for proper UV usage
    elif tool_name == "Bash":
        command = tool_input.get("command", "")
        
        # Check for pip install (should use uv instead)
        if re.search(r'\bpip\s+install\b', command):
            print(json.dumps({
                "decision": "block",
                "reason": (
                    "Use UV instead of pip! Per CLAUDE.md:\n"
                    "  - Install packages: uv add <package>\n"
                    "  - Install dev dependencies: uv add --dev <package>\n"
                    "  - Sync all dependencies: uv sync"
                )
            }))
            return 1
        
        # Check for poetry commands (should use uv)
        if re.search(r'\bpoetry\s+(add|install|remove)\b', command):
            print(json.dumps({
                "decision": "block",
                "reason": (
                    "Use UV instead of Poetry! Per CLAUDE.md:\n"
                    "  - Add package: uv add <package>\n"
                    "  - Remove package: uv remove <package>\n"
                    "  - Install all: uv sync"
                )
            }))
            return 1
        
        # Check for Python execution without venv_linux
        python_patterns = [
            r'^python\s+',
            r'^python3\s+',
            r'^pytest\s+',
            r'^mypy\s+',
            r'^ruff\s+',
        ]
        
        for pattern in python_patterns:
            if re.search(pattern, command):
                # Check if using uv run (which is correct)
                if not command.startswith("uv run"):
                    # Check if venv_linux is mentioned
                    if "venv_linux" not in command and "./venv_linux" not in command:
                        print(json.dumps({
                            "decision": "block",
                            "reason": (
                                "Use UV or venv_linux for Python commands! Per CLAUDE.md:\n"
                                "  Preferred: uv run python script.py\n"
                                "  Or: uv run pytest\n"
                                "  Or: ./venv_linux/bin/python script.py\n"
                                "Always use the virtual environment."
                            )
                        }))
                        return 1
        
        # Warn about manual venv creation
        if re.search(r'python\s+-m\s+venv\b', command):
            print(json.dumps({
                "decision": "block",
                "reason": (
                    "Use UV to manage virtual environments! Per CLAUDE.md:\n"
                    "  Create venv: uv venv\n"
                    "  Use specific Python: uv python install 3.12"
                )
            }))
            return 1
    
    # Approve by default
    print(json.dumps({"decision": "approve"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())