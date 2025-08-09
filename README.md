# Claude Python Hooks 🐍

Automated enforcement of Python development standards for Claude Code based on CLAUDE.md best practices.

## Features

### 🛡️ PreToolUse Hooks (Blocking)

These hooks prevent violations before they happen:

#### 1. **File Structure Enforcement** (`python_file_limits_hook.py`)
- ❌ Blocks files exceeding 500 lines
- ❌ Blocks functions exceeding 50 lines  
- ❌ Blocks classes exceeding 100 lines
- Enforces modular, maintainable code structure

#### 2. **UV Package Management** (`uv_package_management_hook.py`)
- ❌ Blocks direct edits to pyproject.toml dependencies
- ❌ Blocks `pip install` commands
- ❌ Blocks `poetry` commands
- ✅ Enforces `uv add/remove` for all package management
- ✅ Requires virtual environment usage

#### 3. **Search Command Standards** (`search_commands_hook.py`)
- ❌ Blocks `grep` → enforces `rg` (ripgrep)
- ❌ Blocks `find -name` → enforces `rg --files`
- ❌ Blocks `ack`, `ag`, `locate`
- Ensures fast, consistent search operations

#### 4. **Git Commit Standards** (`git_commit_standards_hook.py`)
- ❌ Blocks "Claude Code" or AI references in commits
- ❌ Blocks poorly formatted commit messages
- ❌ Blocks direct pushes to main/master
- ❌ Blocks dangerous `git push --force`
- ✅ Enforces conventional commit format

#### 5. **Testing Standards** (`testing_standards_hook.py`)
- ❌ Blocks test files outside `tests/` directories
- ❌ Blocks incorrectly named test files
- ❌ Blocks `unittest` in favor of `pytest`
- ✅ Enforces vertical slice architecture
- ✅ Promotes TDD practices

### 📝 PostToolUse Hooks (Logging)

These hooks run after operations for logging and tracking:

- **Ruff Linting Check** - Logs linting violations
- **Type Check** - Logs missing type hints
- **Test Reminder** - Logs test coverage gaps
- **Code Quality Reminder** - Tracks modified files

> **Note**: PostToolUse hooks output is logged internally by Claude Code and not displayed to users.

## Installation

### Quick Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/claude-python-hooks.git
cd claude-python-hooks

# Run the setup script
./setup.sh
```

### Manual Setup

1. Set environment variable:
```bash
export CLAUDE_PYTHON_HOOKS_PATH=/path/to/claude-python-hooks
```

2. Copy settings to Claude config:
```bash
cp settings.json ~/.claude/settings.json
```

3. Make hooks executable:
```bash
chmod +x hooks/*.py
```

## Configuration

### Settings Location
- Global: `~/.claude/settings.json`
- Local: `.claude/settings.json` (in project root)

### Customizing Hooks

Edit `settings.json` to enable/disable specific hooks:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PYTHON_HOOKS_PATH/hooks/python_file_limits_hook.py"
          }
        ]
      }
    ]
  }
}
```

### Temporarily Disable

```bash
# Disable all hooks
mv ~/.claude/settings.json ~/.claude/settings.json.disabled

# Re-enable
mv ~/.claude/settings.json.disabled ~/.claude/settings.json
```

## Hook Development

### Creating Custom Hooks

Hooks are Python scripts that:
1. Read JSON from stdin
2. Process the tool input
3. Return JSON decision to stdout

Example hook structure:

```python
#!/usr/bin/env python3
import json
import sys

def main():
    # Read input
    input_data = json.load(sys.stdin)
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    
    # Check conditions
    if should_block(tool_name, tool_input):
        print(json.dumps({
            "decision": "block",
            "reason": "Explanation of why blocked"
        }))
        return 1
    
    # Approve
    print(json.dumps({"decision": "approve"}))
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

### Testing Hooks

Test individual hooks manually:

```bash
echo '{"tool_name": "Bash", "tool_input": {"command": "grep test"}}' | \
  python3 hooks/search_commands_hook.py
```

## Examples

### Blocked Operations

```bash
# Attempting to use grep
$ grep "pattern" file.py
❌ Blocked: Use 'rg' (ripgrep) instead of 'grep'!

# Creating oversized file
$ write large_file.py (600 lines)
❌ Blocked: File would be 600 lines (max 500)

# Using pip
$ pip install requests
❌ Blocked: Use UV instead of pip!
```

### Correct Alternatives

```bash
# Use ripgrep
$ rg "pattern" file.py
✅ Allowed

# Split large files
$ write module1.py (250 lines)
$ write module2.py (250 lines)
✅ Allowed

# Use UV for packages
$ uv add requests
✅ Allowed
```

## CLAUDE.md Integration

These hooks enforce the Python development standards defined in CLAUDE.md:

- **KISS**: Keep It Simple, Stupid
- **YAGNI**: You Aren't Gonna Need It
- **DRY**: Don't Repeat Yourself
- **Single Responsibility Principle**
- **Test-Driven Development**
- **Type Safety with Type Hints**
- **Modular Architecture**

## Troubleshooting

### Hooks Not Triggering

1. Check environment variable:
```bash
echo $CLAUDE_PYTHON_HOOKS_PATH
```

2. Verify hooks are executable:
```bash
ls -la $CLAUDE_PYTHON_HOOKS_PATH/hooks/*.py
```

3. Check Claude settings:
```bash
cat ~/.claude/settings.json
```

4. Restart Claude Code after configuration changes

### Debug Mode

Enable verbose logging by modifying hooks to log to `/tmp/claude_hooks.log`:

```python
import logging
logging.basicConfig(
    filename='/tmp/claude_hooks.log',
    level=logging.DEBUG
)
```

## Contributing

Contributions are welcome! Please:
1. Follow the existing code style
2. Add tests for new hooks
3. Update documentation
4. Submit a pull request

## License

MIT License - See LICENSE file for details

## Acknowledgments

Built for enforcing Python best practices with Claude Code, based on comprehensive CLAUDE.md development standards.

---

**Note**: PostToolUse hooks provide logging only. For user-visible warnings, use PreToolUse hooks that can block operations.