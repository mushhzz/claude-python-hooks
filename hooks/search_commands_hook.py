#!/usr/bin/env python3
"""
Hook to enforce proper search commands per CLAUDE.md.

Enforces:
- Always use rg (ripgrep) instead of grep
- Use rg instead of find -name
- Block traditional search commands
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
    
    # Only check Bash commands
    if tool_name != "Bash":
        print(json.dumps({"decision": "approve"}))
        return 0
    
    command = tool_input.get("command", "")
    
    # Block grep commands (except when piped from other commands)
    if re.match(r'^grep\b(?!.*\|)', command):
        print(json.dumps({
            "decision": "block",
            "reason": (
                "Use 'rg' (ripgrep) instead of 'grep'! Per CLAUDE.md:\n"
                "  - Search pattern: rg 'pattern'\n"
                "  - Search in files: rg 'pattern' *.py\n"
                "  - Case insensitive: rg -i 'pattern'\n"
                "  - Show context: rg -C 3 'pattern'\n"
                "ripgrep is faster and has better features."
            )
        }))
        return 1
    
    # Block find with -name
    if re.search(r'^find\s+\S+\s+-name\b', command):
        print(json.dumps({
            "decision": "block",
            "reason": (
                "Use 'rg' instead of 'find -name'! Per CLAUDE.md:\n"
                "  - Find Python files: rg --files -g '*.py'\n"
                "  - Find all files: rg --files\n"
                "  - Filter by pattern: rg --files | rg 'pattern'\n"
                "ripgrep is much faster for file searches."
            )
        }))
        return 1
    
    # Block ack, ag (silver searcher) - suggest rg
    if re.match(r'^(ack|ag)\b', command):
        print(json.dumps({
            "decision": "block",
            "reason": (
                "Use 'rg' (ripgrep) for searching! Per CLAUDE.md:\n"
                "ripgrep is the standard search tool for this project.\n"
                "It's faster and more feature-rich than ack or ag."
            )
        }))
        return 1
    
    # Warn about locate command
    if re.match(r'^locate\b', command):
        print(json.dumps({
            "decision": "block",
            "reason": (
                "Use 'rg --files' instead of 'locate'!\n"
                "locate uses a database that may be outdated.\n"
                "rg --files gives real-time results."
            )
        }))
        return 1
    
    # Approve by default
    print(json.dumps({"decision": "approve"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())