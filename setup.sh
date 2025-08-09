#!/bin/bash
# Setup script for Claude Python Hooks to enforce CLAUDE.md standards

set -e

echo "🔧 Claude Python Hooks Setup"
echo "============================"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if hooks directory exists
if [ ! -d "$SCRIPT_DIR/hooks" ]; then
    echo "❌ Error: hooks directory not found!"
    exit 1
fi

# Make all hooks executable
echo "📝 Making hooks executable..."
chmod +x "$SCRIPT_DIR/hooks"/*.py

# Set environment variable
export CLAUDE_PYTHON_HOOKS_PATH="$SCRIPT_DIR"
echo "✅ Set CLAUDE_PYTHON_HOOKS_PATH=$CLAUDE_PYTHON_HOOKS_PATH"

# Determine Claude settings directory
CLAUDE_SETTINGS_DIR=""

# Check common locations
if [ -d "$HOME/.claude" ]; then
    CLAUDE_SETTINGS_DIR="$HOME/.claude"
elif [ -d "$HOME/.config/claude" ]; then
    CLAUDE_SETTINGS_DIR="$HOME/.config/claude"
elif [ -d "$HOME/Library/Application Support/Claude" ]; then
    CLAUDE_SETTINGS_DIR="$HOME/Library/Application Support/Claude"
else
    echo "⚠️  Could not find Claude settings directory."
    echo "Please create one of these directories:"
    echo "  - $HOME/.claude"
    echo "  - $HOME/.config/claude"
    read -p "Create $HOME/.claude? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        mkdir -p "$HOME/.claude"
        CLAUDE_SETTINGS_DIR="$HOME/.claude"
    else
        echo "❌ Setup cancelled"
        exit 1
    fi
fi

echo "📂 Using Claude settings directory: $CLAUDE_SETTINGS_DIR"

# Backup existing settings if they exist
if [ -f "$CLAUDE_SETTINGS_DIR/settings.json" ]; then
    BACKUP_FILE="$CLAUDE_SETTINGS_DIR/settings.json.backup.$(date +%Y%m%d_%H%M%S)"
    echo "💾 Backing up existing settings to: $BACKUP_FILE"
    cp "$CLAUDE_SETTINGS_DIR/settings.json" "$BACKUP_FILE"
fi

# Copy settings.json
echo "📋 Installing settings.json..."
sed "s|\$CLAUDE_PYTHON_HOOKS_PATH|$SCRIPT_DIR|g" "$SCRIPT_DIR/settings.json" > "$CLAUDE_SETTINGS_DIR/settings.json"

# Add to shell profile
echo ""
echo "🔗 Adding to shell profile..."

# Detect shell and profile file
if [ -n "$ZSH_VERSION" ]; then
    PROFILE_FILE="$HOME/.zshrc"
elif [ -n "$BASH_VERSION" ]; then
    PROFILE_FILE="$HOME/.bashrc"
else
    PROFILE_FILE="$HOME/.profile"
fi

# Check if already added
if ! grep -q "CLAUDE_PYTHON_HOOKS_PATH" "$PROFILE_FILE" 2>/dev/null; then
    echo "" >> "$PROFILE_FILE"
    echo "# Claude Python Hooks" >> "$PROFILE_FILE"
    echo "export CLAUDE_PYTHON_HOOKS_PATH=\"$SCRIPT_DIR\"" >> "$PROFILE_FILE"
    echo "✅ Added to $PROFILE_FILE"
else
    echo "✅ Already in $PROFILE_FILE"
fi

# Create README
cat > "$SCRIPT_DIR/README.md" << 'EOF'
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
EOF

echo ""
echo "✅ Setup complete!"
echo ""
echo "📚 What's been configured:"
echo "  • File size enforcement (500 lines max)"
echo "  • Function/class size limits (50/100 lines)"
echo "  • UV package management enforcement"
echo "  • Search command standards (rg over grep)"
echo "  • Git commit message standards"
echo "  • Testing structure requirements"
echo ""
echo "🚀 Next steps:"
echo "  1. Restart your shell or run: source $PROFILE_FILE"
echo "  2. Start Claude Code and the hooks will be active"
echo ""
echo "📖 See README.md for more information"