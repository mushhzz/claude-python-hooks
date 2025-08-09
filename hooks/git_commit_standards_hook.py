#!/usr/bin/env python3
"""
Hook to enforce Git commit standards per CLAUDE.md.

Enforces:
- No "claude code" or "written by claude" in commit messages
- Proper commit message format
- No committing without explicit user request
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
    
    # Only check Bash commands for git operations
    if tool_name != "Bash":
        print(json.dumps({"decision": "approve"}))
        return 0
    
    command = tool_input.get("command", "")
    
    # FIRST: Check current branch - block commits to main/master
    if re.search(r'\bgit\s+commit\b', command):
        # Get current branch
        try:
            import subprocess
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                timeout=5
            )
            current_branch = result.stdout.strip()
            
            if current_branch in ["main", "master", "production"]:
                print(json.dumps({
                    "decision": "block",
                    "reason": (
                        "❌ NEVER commit directly to main/master! Per CLAUDE.md GitHub Flow:\n\n"
                        "1. Create feature branch:\n"
                        "   git checkout -b feature/your-feature\n\n"
                        "2. Make changes and commit to feature branch\n\n"
                        "3. Push feature branch:\n"
                        "   git push origin feature/your-feature\n\n"
                        "4. Create Pull Request for review\n\n"
                        "This ensures code review and prevents breaking production."
                    )
                }))
                return 1
        except:
            # If we can't determine branch, check the command itself
            pass
    
    # Check for git commit commands
    if re.search(r'\bgit\s+commit\b', command):
        # Check for prohibited phrases in commit message
        prohibited_phrases = [
            r'claude\s+code',
            r'written\s+by\s+claude',
            r'generated\s+by\s+claude',
            r'claude\s+ai',
            r'anthropic',
            r'🤖',  # No robot emojis
        ]
        
        command_lower = command.lower()
        for phrase in prohibited_phrases:
            if re.search(phrase, command_lower):
                print(json.dumps({
                    "decision": "block",
                    "reason": (
                        "Never include 'Claude Code' or AI references in commit messages! "
                        "Per CLAUDE.md: Write professional commit messages without "
                        "mentioning AI assistance.\n\n"
                        "Format: <type>(<scope>): <subject>\n"
                        "Types: feat, fix, docs, style, refactor, test, chore"
                    )
                }))
                return 1
        
        # Check commit message format
        if '-m' in command:
            # Extract the commit message
            msg_match = re.search(r'-m\s+["\']([^"\']+)["\']', command)
            if msg_match:
                message = msg_match.group(1)
                
                # Check for conventional commit format
                valid_format = re.match(
                    r'^(feat|fix|docs|style|refactor|test|chore)(\([^)]+\))?:\s+.+',
                    message
                )
                
                if not valid_format:
                    # Allow simple messages if they're descriptive
                    if len(message) < 10:
                        print(json.dumps({
                            "decision": "block",
                            "reason": (
                                "Commit message too short or incorrect format! Per CLAUDE.md:\n"
                                "Format: <type>(<scope>): <subject>\n\n"
                                "Examples:\n"
                                "  feat(auth): add two-factor authentication\n"
                                "  fix(api): resolve timeout issue in payment endpoint\n"
                                "  docs: update API documentation\n"
                                "  refactor(database): optimize query performance"
                            )
                        }))
                        return 1
    
    # Check for git push to protected branches
    if re.search(r'git\s+push', command):
        # Check if pushing to main/master/production directly
        if re.search(r'origin\s+(main|master|production)\b', command) or \
           re.search(r'(main|master|production):(main|master|production)', command):
            print(json.dumps({
                "decision": "block",
                "reason": (
                    "❌ Don't push directly to protected branches! Per CLAUDE.md GitHub Flow:\n\n"
                    "1. Create feature branch:\n"
                    "   git checkout -b feature/name\n\n"
                    "2. Push feature branch:\n" 
                    "   git push origin feature/name\n\n"
                    "3. Create Pull Request\n\n"
                    "4. Review and merge via PR\n\n"
                    "Protected branches: main, master, production"
                )
            }))
            return 1
    
    # Block git merge into protected branches
    if re.search(r'git\s+merge', command):
        try:
            import subprocess
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                timeout=5
            )
            current_branch = result.stdout.strip()
            
            if current_branch in ["main", "master", "production"]:
                print(json.dumps({
                    "decision": "block", 
                    "reason": (
                        "❌ Don't merge directly into protected branches!\n\n"
                        "Use Pull Requests for merging into main/master.\n"
                        "This ensures code review and CI/CD checks."
                    )
                }))
                return 1
        except:
            pass
    
    # Check for dangerous git operations
    if re.search(r'git\s+push\s+.*--force(?!-with-lease)', command):
        print(json.dumps({
            "decision": "block",
            "reason": (
                "Never use 'git push --force'!\n"
                "Use 'git push --force-with-lease' instead for safety.\n"
                "This prevents overwriting others' work."
            )
        }))
        return 1
    
    # Approve by default
    print(json.dumps({"decision": "approve"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())