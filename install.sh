#!/bin/bash
# Installation script for Peer Review MCP Server

set -e

echo "🚀 Installing Peer Review MCP Server..."
echo ""

# Check if already installed
if command -v peer-review-mcp &> /dev/null && peer-review-mcp version &> /dev/null; then
    echo "✅ Package is already installed!"
    peer-review-mcp version
    echo ""
    read -p "Do you want to reinstall? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled."
        exit 0
    fi
fi

# Detect Python command
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ Error: Python 3 is not installed"
    exit 1
fi

echo "✓ Found Python: $PYTHON_CMD"

# Check Python version
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $PYTHON_VERSION"

# Install build dependencies first (helps with corporate SSL issues)
echo ""
echo "📦 Installing build dependencies..."
$PYTHON_CMD -m pip install setuptools wheel --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --upgrade 2>&1 | grep -E "(Successfully|Requirement already satisfied|Installing)"

# Install package
echo ""
echo "📦 Installing package in editable mode..."

if $PYTHON_CMD -m pip install -e . 2>&1 | tee /tmp/pip_install.log | grep -q "SSLError\|certificate verify failed\|subprocess.*did not run successfully"; then
    echo ""
    echo "⚠️  SSL/build error detected. Retrying with trusted hosts..."
    $PYTHON_CMD -m pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -e .
else
    if [ ${PIPESTATUS[0]} -ne 0 ]; then
        echo ""
        echo "⚠️  Installation failed. Retrying with trusted hosts..."
        $PYTHON_CMD -m pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -e .
    fi
fi

echo ""
echo "✓ Installation complete!"
echo ""

# Determine Python version for PATH
PY_VERSION=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
BIN_PATH="$HOME/Library/Python/$PY_VERSION/bin"

# Check if peer-review-mcp is accessible
if ! command -v peer-review-mcp &> /dev/null; then
    echo "⚠️  The 'peer-review-mcp' command is not in your PATH."
    echo ""
    echo "Add this line to your ~/.zshrc or ~/.bash_profile:"
    echo ""
    echo "    export PATH=\"$BIN_PATH:\$PATH\""
    echo ""
    echo "Then run: source ~/.zshrc (or source ~/.bash_profile)"
    echo ""
    
    # Try to add to PATH temporarily
    export PATH="$BIN_PATH:$PATH"
fi

# Test installation
echo "🧪 Testing installation..."
if command -v peer-review-mcp &> /dev/null; then
    peer-review-mcp version
    echo ""
    echo "✅ Installation successful!"
    echo ""
    echo "Next steps:"
    echo "1. Create .env file: cp .env.example .env"
    echo "2. Add your GitHub token to .env"
    echo "3. Run: peer-review-mcp config-check"
    echo "4. Start server: peer-review-mcp start"
else
    echo ""
    echo "❌ Could not verify installation. Please add the bin directory to your PATH manually."
    echo "   Binary location: $BIN_PATH"
fi
