# Peer Review Agentic MCP Server

An advanced Model Context Protocol (MCP) server that automates peer review governance and validation by integrating with Git repositories, SonarQube, and Jira to standardize review criteria and improve turnaround times.

## 🚀 Features

- **Automated Peer Review Analysis**: Comprehensive analysis of pull requests against governance policies
- **Git Integration**: Seamless integration with GitHub for PR triggers and workflow automation
- **Code Quality Assessment**: Integration with SonarQube for automated code quality analysis
- **Issue Tracking**: Jira integration for creating and managing review-related issues
- **Governance Validation**: Enforces organizational policies and coding standards automatically
- **MCP Protocol**: Full Model Context Protocol support for AI agent interactions
- **Real-time Metrics**: Performance dashboards and compliance reporting

## 📋 Prerequisites

- Python 3.8+
- GitHub account with API access
- SonarQube instance (optional)
- Jira instance (optional)

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd peerReviewAgenticMCP
   ```

2. **Install dependencies:**
   ```bash
   pip install -e .
   # or for development
   pip install -e ".[dev]"
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# GitHub Integration
GITHUB_ACCESS_TOKEN=your_github_token_here
GITHUB_WEBHOOK_SECRET=your_webhook_secret_here

# SonarQube Integration (Optional)
SONARQUBE_URL=https://your-sonarqube-instance.com
SONARQUBE_TOKEN=your_sonarqube_token_here

# Jira Integration (Optional)
JIRA_URL=https://your-company.atlassian.net
JIRA_USERNAME=your_jira_email@company.com
JIRA_API_TOKEN=your_jira_api_token_here

# Peer Review Configuration
PEER_REVIEW_MIN_REVIEWERS=2
PEER_REVIEW_REVIEW_TIMEOUT_HOURS=48

# MCP Server Configuration
MCP_HOST=127.0.0.1
MCP_PORT=8000
MCP_DEBUG=false
MCP_LOG_LEVEL=INFO
```

### GitHub Setup

1. **Create a Personal Access Token:**
   - Go to GitHub Settings > Developer settings > Personal access tokens
   - Generate a new token with the following scopes:
     - `repo` (Full control of private repositories)
     - `read:org` (Read org and team membership)
     - `user:email` (Access user email addresses)

2. **Set up Webhook (Optional):**
   - In your repository settings, add a webhook pointing to your MCP server
   - Events to subscribe: Pull requests, Pull request reviews, Check runs

### SonarQube Setup

1. **Generate User Token:**
   - Login to SonarQube
   - Go to My Account > Security > Generate Tokens
   - Create a token with analysis permissions

2. **Project Configuration:**
   - Ensure your projects are configured in SonarQube
   - Project keys should match repository names (or configure mapping)

### Jira Setup

1. **Create API Token:**
   - Go to Atlassian Account Settings
   - Create an API token
   - Use your email and token for authentication

## 🚀 Usage

### Starting the MCP Server

```bash
# Start the server
python -m peer_review_mcp.server

# Or using the CLI
peer-review-mcp --host 0.0.0.0 --port 8000
```

### MCP Tools

The server provides the following MCP tools:

#### 1. `analyze_pull_request`
Analyze a pull request for compliance and review criteria.

```json
{
  "repository": "owner/repo",
  "pr_number": 123
}
```

#### 2. `get_review_summary`
Get a summary of pull request review status.

```json
{
  "repository": "owner/repo",
  "pr_number": 123
}
```

#### 3. `validate_governance`
Validate pull request against governance policies.

```json
{
  "repository": "owner/repo",
  "pr_number": 123
}
```

#### 4. `get_review_metrics`
Get review performance metrics for a repository.

```json
{
  "repository": "owner/repo",
  "days": 30
}
```

#### 5. `trigger_automated_checks`
Trigger automated checks for a pull request.

```json
{
  "repository": "owner/repo",
  "pr_number": 123,
  "check_types": ["build", "test", "code_quality"]
}
```

#### 6. `create_jira_issue`
Create a Jira issue for review findings.

```json
{
  "repository": "owner/repo",
  "pr_number": 123,
  "issue_type": "Task",
  "priority": "Medium"
}
```

### MCP Resources

The server exposes the following resources:

- `peer-review://repositories` - List of tracked repositories
- `peer-review://pull-requests` - Active pull requests
- `peer-review://review-criteria` - Governance and review criteria
- `peer-review://metrics` - Review performance metrics

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   MCP Client    │◄──►│   MCP Server     │◄──►│   Database      │
│  (AI Agent)     │    │ (Peer Review)    │    │  (SQLite/PG)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
         ┌──────▼─────┐ ┌────────▼─────┐ ┌─────▼─────┐
         │  GitHub    │ │  SonarQube   │ │   Jira    │
         │Integration │ │ Integration  │ │Integration│
         └────────────┘ └──────────────┘ └───────────┘
```

### Components

- **MCP Server**: Core server implementing the Model Context Protocol
- **Peer Review Engine**: Analyzes PRs and enforces governance policies
- **Database Manager**: Handles data persistence and retrieval
- **Integrations**: Connectors for GitHub, SonarQube, and Jira
- **Governance Agent**: AI agent for policy validation and enforcement

## 📊 Governance Policies

The server enforces various governance policies:

### Branch Naming Conventions
- `feature/[description]` - New features
- `bugfix/[description]` - Bug fixes
- `hotfix/[description]` - Critical fixes
- `release/v[version]` - Release branches

### Commit Message Standards
- Follow conventional commit format: `type(scope): description`
- Minimum 10 characters, maximum 72 characters
- Types: feat, fix, docs, style, refactor, test, chore

### PR Size Limits
- Maximum 50 files changed per PR
- Maximum 500 lines changed per PR
- Recommendations for large PRs to be split

### Code Quality Requirements
- Minimum 80% test coverage
- SonarQube quality gate must pass
- Security scans must be completed

### Review Requirements
- Minimum 2 reviewer approvals
- No blocking reviews (changes requested)
- Required labels present
- No blocked labels present

## 🔧 Development

### Project Structure

```
src/peer_review_mcp/
├── __init__.py
├── server.py              # Main MCP server
├── config.py              # Configuration management
├── models/                # Data models and schemas
│   └── __init__.py
├── services/              # Business logic services
│   ├── __init__.py
│   ├── database.py        # Database management
│   └── peer_review.py     # Review engine
├── integrations/          # External service integrations
│   ├── __init__.py
│   ├── github.py          # GitHub integration
│   ├── sonarqube.py       # SonarQube integration
│   └── jira.py            # Jira integration
└── agents/                # AI agents
    ├── __init__.py
    └── governance.py      # Governance validation agent
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=peer_review_mcp

# Run specific test file
pytest tests/test_server.py
```

### Code Quality

```bash
# Format code
black src/

# Sort imports
isort src/

# Type checking
mypy src/

# Linting
flake8 src/
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

## 📈 Monitoring and Metrics

### Health Checks

The server provides health check endpoints:

- `/health` - Basic health status
- `/metrics` - Prometheus-style metrics

### Metrics Tracked

- Pull request processing time
- Compliance score distribution
- Policy violation frequency
- Integration response times
- Review turnaround time

## 🔒 Security

### Best Practices

1. **API Tokens**: Store all tokens securely in environment variables
2. **Webhook Validation**: Always validate webhook signatures
3. **Access Control**: Use least-privilege principle for API access
4. **Data Encryption**: Encrypt sensitive data at rest
5. **Audit Logging**: Enable comprehensive audit logging

### Security Scans

The server includes security validation:

- Secret detection in code changes
- Dependency vulnerability scanning
- Security policy enforcement
- Compliance reporting

## 🐛 Troubleshooting

### Common Issues

1. **GitHub API Rate Limits**
   - Use authenticated requests with personal access tokens
   - Implement proper rate limiting and retry logic
   - Consider GitHub App authentication for higher limits

2. **SonarQube Connection Issues**
   - Verify SonarQube URL and credentials
   - Check network connectivity and firewall rules
   - Ensure project exists in SonarQube

3. **Jira Authentication Failures**
   - Verify API token is valid and not expired
   - Check user permissions for project access
   - Ensure Jira URL is correct

4. **Database Connection Issues**
   - Verify database URL format
   - Check database permissions and connectivity
   - Initialize database tables if needed

### Debug Mode

Enable debug mode for detailed logging:

```bash
MCP_DEBUG=true MCP_LOG_LEVEL=DEBUG python -m peer_review_mcp.server
```

## 📝 API Reference

### Server Configuration

The server accepts the following command-line arguments:

```bash
peer-review-mcp --help
```

### Environment Variables Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GITHUB_ACCESS_TOKEN` | GitHub personal access token | None | Yes |
| `GITHUB_WEBHOOK_SECRET` | GitHub webhook secret | None | No |
| `SONARQUBE_URL` | SonarQube server URL | None | No |
| `SONARQUBE_TOKEN` | SonarQube authentication token | None | No |
| `JIRA_URL` | Jira server URL | None | No |
| `JIRA_USERNAME` | Jira username/email | None | No |
| `JIRA_API_TOKEN` | Jira API token | None | No |
| `MCP_HOST` | Server host address | 127.0.0.1 | No |
| `MCP_PORT` | Server port number | 8000 | No |
| `MCP_DEBUG` | Enable debug mode | false | No |
| `DB_URL` | Database connection URL | sqlite:///peer_review.db | No |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋‍♂️ Support

For support and questions:

- Create an issue in the GitHub repository
- Check the documentation and troubleshooting guide
- Review existing issues for similar problems

## 🗺️ Roadmap

- [ ] Support for GitLab and Bitbucket
- [ ] Advanced AI-powered code review suggestions
- [ ] Integration with more security tools
- [ ] Custom policy definition UI
- [ ] Multi-repository governance dashboards
- [ ] Slack/Teams notifications
- [ ] Advanced analytics and reporting
- [ ] Docker containerization
- [ ] Kubernetes deployment manifests