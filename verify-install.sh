#!/bin/bash
# Verification script for Peer Review MCP Server installation

set -e

echo "🔍 Checking Peer Review MCP Server Installation"
echo "================================================"
echo ""

# Add PATH
export PATH="$HOME/Library/Python/3.12/bin:$PATH"

# Check if package is installed
echo "📦 Package Status:"
if python3 -m pip show peer-review-agentic-mcp &> /dev/null; then
    INSTALLED_VERSION=$(python3 -m pip show peer-review-agentic-mcp | grep Version | cut -d' ' -f2)
    EDITABLE_LOC=$(python3 -m pip show peer-review-agentic-mcp | grep "Editable project location" | cut -d: -f2- | xargs)
    echo "   ✅ Installed: v$INSTALLED_VERSION"
    if [ ! -z "$EDITABLE_LOC" ]; then
        echo "   ✅ Editable Mode: $EDITABLE_LOC"
    fi
else
    echo "   ❌ Not installed"
    echo ""
    echo "Run: ./install.sh"
    exit 1
fi

echo ""

# Check if command is accessible
echo "🔧 Command Accessibility:"
if command -v peer-review-mcp &> /dev/null; then
    echo "   ✅ peer-review-mcp command found"
    peer-review-mcp version
else
    echo "   ❌ peer-review-mcp command not in PATH"
    echo ""
    echo "Add to PATH:"
    echo "   export PATH=\"\$HOME/Library/Python/3.12/bin:\$PATH\""
    echo ""
    echo "Make it permanent:"
    echo "   echo 'export PATH=\"\$HOME/Library/Python/3.12/bin:\$PATH\"' >> ~/.zshrc"
    echo "   source ~/.zshrc"
    exit 1
fi

echo ""

# Check configuration
echo "⚙️  Configuration Status:"
peer-review-mcp config-check

echo ""
echo "================================================"
echo "✅ Installation verification complete!"
echo ""
echo "Next steps:"
if ! grep -q "GITHUB_ACCESS_TOKEN" .env 2>/dev/null || [ ! -f .env ]; then
    echo "1. Configure GitHub token:"
    echo "   cp .env.example .env"
    echo "   # Edit .env and add your GitHub token"
else
    echo "1. ✅ Configuration file exists"
fi
echo "2. Start the server:"
echo "   peer-review-mcp start"
echo ""
echo "For MCP client integration, see QUICKSTART.md"
