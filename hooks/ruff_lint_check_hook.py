#!/usr/bin/env python3
"""
Post-tool-use hook to enforce ruff linting after Python file modifications.

Runs after Write/Edit operations on Python files and reminds to run ruff.
"""

import json
import sys
import os
import subprocess
from pathlib import Path


def check_ruff_installed():
    """Check if ruff is available in the project."""
    try:
        # Try uv run ruff first
        result = subprocess.run(
            ["uv", "run", "ruff", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return "uv"
    except:
        pass
    
    try:
        # Try ruff directly
        result = subprocess.run(
            ["ruff", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return "direct"
    except:
        pass
    
    return None


def run_ruff_check(file_path: str, ruff_mode: str):
    """Run ruff check on the file and return violations."""
    if ruff_mode == "uv":
        cmd = ["uv", "run", "ruff", "check", file_path, "--output-format", "json"]
    else:
        cmd = ["ruff", "check", file_path, "--output-format", "json"]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            return None  # No violations
        
        # Parse JSON output
        try:
            violations = json.loads(result.stdout)
            return violations
        except:
            # Fallback to text output
            return result.stdout
            
    except Exception as e:
        return f"Error running ruff: {e}"


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
    
    # Only check Python files
    if not file_path.endswith(".py"):
        print(json.dumps({"decision": "approve"}))
        return 0
    
    # Check if file exists (it should after Write/Edit)
    if not os.path.exists(file_path):
        print(json.dumps({"decision": "approve"}))
        return 0
    
    # Check if ruff is available
    ruff_mode = check_ruff_installed()
    if not ruff_mode:
        print(json.dumps({
            "decision": "approve",
            "reason": (
                "REMINDER: Install ruff for linting! Per CLAUDE.md:\n"
                "  uv add --dev ruff\n"
                "Then run: uv run ruff check ."
            )
        }))
        return 0
    
    # Run ruff check
    violations = run_ruff_check(file_path, ruff_mode)
    
    if violations is None:
        # No violations
        print(json.dumps({"decision": "approve"}))
        return 0
    
    # Format violation message
    if isinstance(violations, list):
        # JSON format
        violation_msgs = []
        for v in violations[:5]:  # Show first 5 violations
            location = f"{v.get('filename', '')}:{v.get('location', {}).get('row', '')}:{v.get('location', {}).get('column', '')}"
            code = v.get('code', '')
            message = v.get('message', '')
            violation_msgs.append(f"  {location} {code}: {message}")
        
        if len(violations) > 5:
            violation_msgs.append(f"  ... and {len(violations) - 5} more violations")
        
        violation_text = "\n".join(violation_msgs)
    else:
        violation_text = str(violations)[:500]  # Limit output
    
    # Don't block, but strongly remind
    print(json.dumps({
        "decision": "approve", 
        "reason": (
            f"⚠️ RUFF VIOLATIONS DETECTED in {os.path.basename(file_path)}!\n\n"
            f"{violation_text}\n\n"
            "Per CLAUDE.md, you MUST run:\n"
            f"  {'uv run ' if ruff_mode == 'uv' else ''}ruff check --fix {file_path}\n"
            f"  {'uv run ' if ruff_mode == 'uv' else ''}ruff format {file_path}\n\n"
            "Fix these issues before continuing!"
        )
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())