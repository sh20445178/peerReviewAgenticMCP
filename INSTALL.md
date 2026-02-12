# Installation Guide

## Local Development Installation (macOS/Linux)

### Prerequisites
- Python 3.8 or higher
- Git

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/techieshailesh/peerReviewAgenticMCP.git
   cd peerReviewAgenticMCP
   ```

2. **Install in editable mode**

   **For macOS users** (if `pip` command is not found):
   ```bash
   python3 -m pip install -e .
   ```

   **If behind corporate firewall/proxy with SSL issues**:
   
   First, install build dependencies:
   ```bash
   python3 -m pip install setuptools wheel --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --upgrade
   ```
   
   Then install the package:
   ```bash
   python3 -m pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -e .
   ```

   **Standard installation** (if pip is in PATH):
   ```bash
   pip install -e .
   ```

3. **Add to PATH** (macOS)

   The installation script will install the CLI to `~/Library/Python/3.12/bin/`. Add this to your PATH:
   
   ```bash
   echo 'export PATH="$HOME/Library/Python/3.12/bin:$PATH"' >> ~/.zshrc
   source ~/.zshrc
   ```

4. **Verify installation**
   ```bash
   peer-review-mcp --help
   peer-review-mcp version
   ```

## Configuration

1. **Create .env file**
   ```bash
   cp .env.example .env
   ```

2. **Edit .env with your credentials**
   ```bash
   # Required
   GITHUB_ACCESS_TOKEN=ghp_your_token_here

   # Optional
   SONARQUBE_URL=https://sonarqube.example.com
   SONARQUBE_TOKEN=your_token
   
   JIRA_URL=https://your-company.atlassian.net
   JIRA_USERNAME=your.email@company.com
   JIRA_API_TOKEN=your_jira_token
   ```

3. **Check configuration**
   ```bash
   peer-review-mcp config-check
   ```

## Running the Server

### Standalone Mode
```bash
peer-review-mcp start
```

### Docker Mode

1. **Build the image**
   ```bash
   docker build -t peer-review-mcp .
   ```

2. **Run with docker-compose**
   ```bash
   docker-compose up -d
   ```

## Integration with MCP Clients

### Claude Desktop Configuration

Add to your Claude Desktop config file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "peer-review": {
      "command": "/Users/YOUR_USERNAME/Library/Python/3.12/bin/peer-review-mcp",
      "args": ["start"],
      "env": {
        "GITHUB_ACCESS_TOKEN": "your_token_here"
      }
    }
  }
}
```

Replace `YOUR_USERNAME` with your actual username.

### Cline/Other MCP Clients

Configure similarly based on the client's MCP server configuration format.

## Troubleshooting

### Command not found: pip
Use `python3 -m pip` instead of `pip` directly:
```bash
python3 -m pip install -e .
```

### SSL Certificate Errors / Build Dependencies Error
If you see "pip subprocess to install build dependencies did not run successfully" or "subprocess-exited-with-error", install build tools first:
```bash
python3 -m pip install setuptools wheel --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --upgrade
python3 -m pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -e .
```

### Check if Already Installed
Before reinstalling, verify current installation:
```bash
python3 -m pip show peer-review-agentic-mcp
export PATH="$HOME/Library/Python/3.12/bin:$PATH"
peer-review-mcp --help
```

If the package is already installed and working, you don't need to reinstall!

### peer-review-mcp command not found
Ensure Python bin directory is in your PATH:
```bash
export PATH="$HOME/Library/Python/3.12/bin:$PATH"
```

### Import errors after installation
Reinstall the package:
```bash
python3 -m pip install -e . --force-reinstall
```

## Uninstallation

```bash
python3 -m pip uninstall peer-review-agentic-mcp
```
