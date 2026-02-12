# Quick Start Guide

## One-Line Installation (Corporate Environment)

```bash
python3 -m pip install setuptools wheel --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --upgrade && \
python3 -m pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -e . && \
export PATH="$HOME/Library/Python/3.12/bin:$PATH"
```

## Verify Installation

```bash
peer-review-mcp --help
```

## Add to PATH Permanently

```bash
echo 'export PATH="$HOME/Library/Python/3.12/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

## Quick Configuration

```bash
# 1. Create config
cp .env.example .env

# 2. Add your GitHub token
echo "GITHUB_ACCESS_TOKEN=ghp_your_token_here" >> .env

# 3. Verify
peer-review-mcp config-check
```

## Start Server

```bash
peer-review-mcp start
```

## Common Issues

| Error | Solution |
|-------|----------|
| `command not found: pip` | Use `python3 -m pip` instead |
| `pip subprocess...did not run successfully`<br>`subprocess-exited-with-error`<br>`BackendUnavailable` | **First, check if already installed:** `python3 -m pip show peer-review-agentic-mcp`<br>If not installed, run: `python3 -m pip install setuptools wheel --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --upgrade` then retry installation |
| `SSLError` or `certificate verify failed` | Add `--trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org` to all pip commands |
| `command not found: peer-review-mcp` | Add to PATH: `export PATH="$HOME/Library/Python/3.12/bin:$PATH"` |
| Import errors after updates | Run `python3 -m pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -e . --force-reinstall --no-deps` |

## MCP Client Integration

### Claude Desktop (macOS)

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "peer-review": {
      "command": "/Users/YOUR_USERNAME/Library/Python/3.12/bin/peer-review-mcp",
      "args": ["start"],
      "env": {
        "GITHUB_ACCESS_TOKEN": "ghp_your_token_here"
      }
    }
  }
}
```

Replace `YOUR_USERNAME` with your actual macOS username (run `whoami` to check).

## Available Commands

```bash
peer-review-mcp --help          # Show all commands
peer-review-mcp version         # Show version
peer-review-mcp config-check    # Verify configuration
peer-review-mcp start           # Start MCP server
```

## Testing the Server

Once started, the server provides these MCP tools:
- `analyze_pull_request` - Analyze a PR for compliance
- `get_review_summary` - Get review status summary  
- `config_check` - Verify server configuration

See full documentation in [README.md](README.md)
