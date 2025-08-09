# Claude Python Hooks

Hooks to enforce Python development standards from CLAUDE.md.

## Features

### 🔍 Search Command Enforcement
- Blocks `grep` - enforces `rg` (ripgrep)
- Blocks `find -name` - enforces `rg --files`

### 📏 Code Structure Limits
- Files: max 500 lines
- Functions: max 50 lines  
- Classes: max 100 lines

### 📦 UV Package Management
- Blocks direct pyproject.toml edits for dependencies
- Enforces `uv add/remove` commands
- Requires virtual environment usage

### 🔀 Git Standards
- Blocks "Claude Code" in commit messages
- Enforces conventional commit format
- Prevents direct pushes to main/master

### 🧪 Testing Requirements
- Enforces tests/ subdirectory structure
- Requires test_ prefix for test files
- Suggests pytest with coverage

## Usage

Hooks run automatically when using Claude Code. They will:
- ✅ Approve valid operations
- ❌ Block violations with helpful messages
- 💡 Suggest correct alternatives

## Configuration

Settings are in `~/.claude/settings.json`

To disable temporarily:
```bash
mv ~/.claude/settings.json ~/.claude/settings.json.disabled
```

To re-enable:
```bash
mv ~/.claude/settings.json.disabled ~/.claude/settings.json
```

## Testing Hooks Manually

```bash
# Test a hook
echo '{"tool_name": "Bash", "tool_input": {"command": "grep pattern file.txt"}}' | \
  python hooks/search_commands_hook.py
```

## Troubleshooting

If hooks aren't working:
1. Check `CLAUDE_PYTHON_HOOKS_PATH` is set
2. Verify hooks are executable: `chmod +x hooks/*.py`
3. Check Claude settings: `cat ~/.claude/settings.json`
