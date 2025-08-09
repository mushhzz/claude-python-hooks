#!/usr/bin/env python3
"""
Comprehensive post-tool-use hook that reminds about code quality checks.

Tracks modified Python files and reminds to run quality checks before completion.
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime


# Track modified files in a session
MODIFIED_FILES_PATH = "/tmp/claude_modified_python_files.json"


def load_modified_files():
    """Load the list of modified files in this session."""
    if os.path.exists(MODIFIED_FILES_PATH):
        try:
            with open(MODIFIED_FILES_PATH, 'r') as f:
                data = json.load(f)
                # Check if session is recent (within 1 hour)
                if "timestamp" in data:
                    ts = datetime.fromisoformat(data["timestamp"])
                    if (datetime.now() - ts).seconds < 3600:
                        return set(data.get("files", []))
        except:
            pass
    return set()


def save_modified_files(files):
    """Save the list of modified files."""
    try:
        with open(MODIFIED_FILES_PATH, 'w') as f:
            json.dump({
                "files": list(files),
                "timestamp": datetime.now().isoformat()
            }, f)
    except:
        pass


def get_project_root(file_path):
    """Find the project root (directory with pyproject.toml or .git)."""
    path = Path(file_path).parent
    
    for _ in range(10):  # Max 10 levels up
        if (path / "pyproject.toml").exists() or (path / ".git").exists():
            return str(path)
        if path.parent == path:
            break
        path = path.parent
    
    return str(Path(file_path).parent)


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
    
    # Only track Write/Edit/MultiEdit on Python files
    if tool_name not in ["Write", "Edit", "MultiEdit"]:
        print(json.dumps({"decision": "approve"}))
        return 0
    
    file_path = tool_input.get("file_path", "")
    
    # Only track Python files
    if not file_path.endswith(".py"):
        print(json.dumps({"decision": "approve"}))
        return 0
    
    # Load and update modified files
    modified_files = load_modified_files()
    modified_files.add(file_path)
    save_modified_files(modified_files)
    
    # Don't remind on every file, only after multiple modifications
    if len(modified_files) < 3:
        print(json.dumps({"decision": "approve"}))
        return 0
    
    # Find project root
    project_root = get_project_root(file_path)
    
    # Create reminder message
    files_list = "\n".join(f"  - {os.path.basename(f)}" for f in list(modified_files)[:5])
    if len(modified_files) > 5:
        files_list += f"\n  ... and {len(modified_files) - 5} more files"
    
    print(json.dumps({
        "decision": "approve",
        "reason": (
            f"📋 QUALITY CHECK REMINDER - {len(modified_files)} Python files modified!\n\n"
            f"Modified files:\n{files_list}\n\n"
            "Per CLAUDE.md, run these checks before finishing:\n\n"
            "1. LINTING & FORMATTING:\n"
            f"   uv run ruff check {project_root} --fix\n"
            f"   uv run ruff format {project_root}\n\n"
            "2. TYPE CHECKING:\n"
            f"   uv run mypy {project_root}\n\n"
            "3. RUN TESTS:\n"
            f"   uv run pytest\n"
            f"   uv run pytest --cov=src --cov-report=html\n\n"
            "4. CHECK LINE LIMITS:\n"
            "   - Files < 500 lines\n"
            "   - Functions < 50 lines\n"
            "   - Classes < 100 lines\n\n"
            "Complete ALL checks before marking task as done!"
        )
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())