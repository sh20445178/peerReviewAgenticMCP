# Peer Review MCP Tool Layer (TypeScript)

A comprehensive Model Context Protocol (MCP) tool layer built in TypeScript that automates peer review workflows by integrating with GitHub, SonarQube, and build systems. Designed for AI agents to perform deep code reviews, static analysis, build validation, and governance reporting.

## 🚀 Features

### 8 Specialized MCP Tools

1. **`read_pr_changes`**: Read PR metadata and all changed files with diffs
2. **`fetch_file_content`**: Fetch full file content at any git ref for deep review
3. **`run_sonar_scanner`**: Execute SonarQube static analysis and retrieve quality metrics
4. **`validate_build`**: Run configurable build/test pipelines with detailed step results
5. **`write_code_suggestions`**: Post GitHub PR suggestions with one-click apply
6. **`post_ai_review_comments`**: Submit AI-generated PR reviews (APPROVE/REQUEST_CHANGES/COMMENT)
7. **`update_github_check`**: Create/update GitHub Check Runs with pass/fail status
8. **`generate_governance_report`**: Generate post-merge compliance reports with approval metrics

### Key Benefits

- **Automated Code Review**: AI agents can review PRs end-to-end
- **Static Analysis Integration**: SonarQube metrics and issue reporting
- **Build Validation**: Multi-step build verification before merge
- **Governance Compliance**: Audit-ready reports with approval tracking
- **GitHub Native**: Full GitHub REST API integration (Checks, Reviews, Suggestions)

## 📋 Prerequisites

- **Node.js**: 18+ (with npm)
- **GitHub**: Personal access token with `repo` scope
- **SonarQube**: (Optional) Server URL + authentication token
- **sonar-scanner**: (Optional) CLI tool installed and in PATH

## 🛠️ Installation

```bash
cd mcp-tools-ts
npm install
npm run build
```

## ⚙️ Configuration

Create `.env` file in `mcp-tools-ts/` directory:

```bash
# ── GitHub ─────────────────────────────────────────────────────
# Personal access token (needs repo + checks + pull_requests scopes)
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx

# Override for GitHub Enterprise (leave blank for github.com)
GITHUB_API_URL=https://api.github.com

# ── SonarQube ───────────────────────────────────────────────────
# SonarQube or SonarCloud server URL
SONAR_URL=http://localhost:9000

# Preferred: user token (token-only auth)
SONAR_TOKEN=sqp_xxxxxxxxxxxxxxxxxxxx

# Alternative: username/password auth
# SONAR_USERNAME=admin
# SONAR_PASSWORD=admin
```

### GitHub Token Setup

1. Go to **GitHub Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
2. Generate new token with scopes:
   - `repo` (full control)
   - `write:checks` (create check runs)
   - `pull_request` (review PRs)
3. Copy token to `.env` as `GITHUB_TOKEN`

### SonarQube Setup (Optional)

1. Login to SonarQube instance
2. Go to **My Account** → **Security** → **Generate Tokens**
3. Create token with **Execute Analysis** permission
4. Copy token to `.env` as `SONAR_TOKEN`
5. Install `sonar-scanner` CLI:
   ```bash
   # macOS
   brew install sonar-scanner
   
   # Linux
   wget https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/...
   ```
   - Go to Atlassian Account Settings
   - Create an API token


## 🚀 Usage

### Starting the MCP Server

```bash
cd mcp-tools-ts

# Development mode (with auto-reload)
npm run dev

# Production mode
npm run build
npm start
```

The server runs on **stdio** transport (standard input/output) for MCP clients.

### Connecting from MCP Clients

Configure your MCP client (e.g., Claude Desktop, Cline) to invoke the server:

```json
{
  "mcpServers": {
    "peer-review": {
      "command": "node",
      "args": ["/absolute/path/to/mcp-tools-ts/dist/index.js"],
      "env": {
        "GITHUB_TOKEN": "ghp_your_token",
        "SONAR_URL": "http://localhost:9000",
        "SONAR_TOKEN": "sqp_your_token"
      }
    }
  }
}
```

## 📚 Tool Reference

### 1. `read_pr_changes`

Reads pull request metadata and all changed files with diffs.

**Input:**
```json
{
  "repository": "owner/repo",
  "pr_number": 42,
  "include_patch": true
}
```

**Output:** PR details, file list, additions/deletions, patches

**Use case:** First step in any PR review workflow

---

### 2. `fetch_file_content`

Fetches full source file content at a specific git ref.

**Input:**
```json
{
  "repository": "owner/repo",
  "path": "src/server.ts",
  "ref": "main"
}
```

**Output:** Full UTF-8 decoded file content

**Use case:** Deep review of individual files beyond just diffs

---

### 3. `run_sonar_scanner`

Runs SonarScanner CLI, waits for analysis completion, returns quality metrics.

**Input:**
```json
{
  "project_key": "my-project",
  "project_base_dir": "/path/to/source",
  "branch": "feature/new-feature",
  "poll_timeout_seconds": 300
}
```

**Output:** Quality gate status, bugs, vulnerabilities, coverage, issues list

**Use case:** Static code analysis during PR validation

---

### 4. `validate_build`

Executes ordered build/test steps, captures output and exit codes.

**Input:**
```json
{
  "repository": "owner/repo",
  "ref": "abc123",
  "working_directory": "/path/to/checkout",
  "steps": [
    {
      "name": "Install dependencies",
      "command": "npm ci",
      "timeout_seconds": 120
    },
    {
      "name": "Run tests",
      "command": "npm test",
      "timeout_seconds": 300
    }
  ],
  "stop_on_first_failure": true
}
```

**Output:** Per-step exit code, stdout, stderr, duration

**Use case:** Verify PR doesn't break the build

---

### 5. `write_code_suggestions`

Posts code suggestions as GitHub PR review comments with clickable "Apply" button.

**Input:**
```json
{
  "repository": "owner/repo",
  "pr_number": 42,
  "commit_id": "abc123",
  "suggestions": [
    {
      "file": "src/app.ts",
      "start_line": 10,
      "end_line": 12,
      "suggested_code": "const result = await doSomething();",
      "rationale": "Use async/await for better readability",
      "category": "style",
      "severity": "low"
    }
  ],
  "post_as_review": true
}
```

**Output:** Posted suggestions count, generated timestamp

**Use case:** AI-driven code improvement suggestions

---

### 6. `post_ai_review_comments`

Submits a complete PR review with verdict and inline comments.

**Input:**
```json
{
  "repository": "owner/repo",
  "pr_number": 42,
  "commit_id": "abc123",
  "review_body": "## AI Review Summary\n\nFound 3 issues...",
  "verdict": "REQUEST_CHANGES",
  "inline_comments": [
    {
      "path": "src/app.ts",
      "line": 25,
      "body": "Potential null pointer exception here"
    }
  ]
}
```

**Verdicts:** `APPROVE`, `REQUEST_CHANGES`, `COMMENT`

**Output:** Review ID, HTML URL, state

**Use case:** Final AI review submission

---

### 7. `update_github_check`

Creates or updates GitHub Check Runs with pass/fail status.

**Input:**
```json
{
  "repository": "owner/repo",
  "head_sha": "abc123",
  "check_name": "SonarQube Analysis",
  "status": "completed",
  "conclusion": "failure",
  "title": "Quality Gate Failed",
  "summary": "Found 3 critical vulnerabilities",
  "annotations": [
    {
      "path": "src/app.ts",
      "start_line": 42,
      "end_line": 42,
      "annotation_level": "failure",
      "message": "SQL injection vulnerability"
    }
  ]
}
```

**Output:** Check run ID, status, conclusion

**Use case:** Report analysis results in GitHub PR checks UI

---

### 8. `generate_governance_report`

Generates post-merge compliance report with approval metrics.

**Input:**
```json
{
  "repository": "owner/repo",
  "pr_number": 42,
  "sonar_project_key": "my-project",
  "required_approvals": 2,
  "required_checks": ["build", "tests"]
}
```

**Output:** Compliance score, approval count, check results, governance checks

**Use case:** Post-merge audit and compliance tracking

## 🏗️ Architecture

```
┌──────────────────┐
│   MCP Client     │  (AI Agent / Claude)
│   (stdio mode)   │
└────────┬─────────┘
         │
    ┌────▼─────────────────────────────┐
    │  MCP Server (TypeScript/Node.js) │
    │                                   │
    │  ┌─────────────────────────────┐ │
    │  │  8 MCP Tools                │ │
    │  │  • PR Reader                │ │
    │  │  • File Content Fetcher     │ │
    │  │  • Sonar Scanner Runner     │ │
    │  │  • Build Validator          │ │
    │  │  • Code Suggestion Writer   │ │
    │  │  • AI Review Poster         │ │
    │  │  • GitHub Check Updater     │ │
    │  │  • Governance Reporter      │ │
    │  └─────────────────────────────┘ │
    └───┬───────────────┬──────────────┘
        │               │
   ┌────▼────┐    ┌─────▼──────┐
   │ GitHub  │    │ SonarQube  │
   │REST API │    │  REST API  │
   └─────────┘    └────────────┘
```

## 🔧 Development

### Project Structure

```
mcp-tools-ts/
├── src/
│   ├── index.ts              # Entry point
│   ├── server.ts             # MCP server setup & routing
│   ├── types/
│   │   └── index.ts          # Shared TypeScript types
│   ├── utils/
│   │   ├── github-client.ts  # GitHub REST API wrapper
│   │   └── sonar-client.ts   # SonarQube REST API wrapper
│   └── tools/                # 8 MCP tools
│       ├── pr-reader.ts
│       ├── file-content.ts
│       ├── sonar-scanner.ts
│       ├── build-validator.ts
│       ├── code-writer.ts
│       ├── ai-reviewer.ts
│       ├── github-checks.ts
│       └── governance-report.ts
├── package.json
├── tsconfig.json
└── .env.example
```

### Building

```bash
npm run build    # Compile TypeScript → dist/
npm run clean    # Remove dist/
npm run typecheck  # Type check without emitting
```

### Code Quality

```bash
# Type checking
npm run typecheck

# Manual testing (run server locally)
npm run dev
```

## 🎯 Example Workflow

### Complete PR Review Automation

```typescript
// 1. Read PR changes
const prData = await read_pr_changes({
  repository: "owner/repo",
  pr_number: 42
});

// 2. Fetch full file content for detailed review
for (const file of prData.files) {
  const content = await fetch_file_content({
    repository: "owner/repo",
    path: file.filename,
    ref: prData.pr.headSha
  });
  // AI analyzes content...
}

// 3. Run static analysis
const sonarResult = await run_sonar_scanner({
  project_key: "my-project",
  project_base_dir: "/tmp/checkout",
  pr_key: "42",
  pr_branch: prData.pr.headBranch,
  pr_base: prData.pr.baseBranch
});

// 4. Validate build
const buildResult = await validate_build({
  repository: "owner/repo",
  ref: prData.pr.headSha,
  working_directory: "/tmp/checkout",
  steps: [
    { name: "Install", command: "npm ci" },
    { name: "Test", command: "npm test" }
  ]
});

// 5. Generate code suggestions
await write_code_suggestions({
  repository: "owner/repo",
  pr_number: 42,
  commit_id: prData.pr.headSha,
  suggestions: [...] // AI-generated
});

// 6. Post AI review
await post_ai_review_comments({
  repository: "owner/repo",
  pr_number: 42,
  commit_id: prData.pr.headSha,
  review_body: "## Review Summary\n...",
  verdict: buildResult.passed ? "APPROVE" : "REQUEST_CHANGES"
});

// 7. Update GitHub Check
await update_github_check({
  repository: "owner/repo",
  head_sha: prData.pr.headSha,
  check_name: "AI Code Review",
  status: "completed",
  conclusion: "success",
  title: "All checks passed",
  summary: "Build: ✅ | SonarQube: ✅"
});

// 8. After merge: Generate governance report
await generate_governance_report({
  repository: "owner/repo",
  pr_number: 42,
  sonar_project_key: "my-project",
  required_approvals: 2
});
```

## 🔒 Security

- **Token Storage**: All tokens loaded from `.env` (never commit!)
- **Token Scopes**: Use minimal required GitHub scopes
- **Webhook Validation**: Not applicable (server runs on stdio, not HTTP)
- **API Rate Limits**: GitHub allows 5,000 requests/hour for authenticated users

## 🐛 Troubleshooting

### GitHub API Errors

**403 Forbidden**: Check token scopes (`repo`, `write:checks`, `pull_request`)  
**404 Not Found**: Verify repository name format (`owner/repo`)  
**422 Validation Failed**: Check input parameters match schema

### SonarQube Issues

**Connection Refused**: Verify `SONAR_URL` is accessible  
**401 Unauthorized**: Check `SONAR_TOKEN` is valid  
**sonar-scanner not found**: Install CLI tool (`brew install sonar-scanner`)

### Build Validation Failures

**Timeout**: Increase `timeout_seconds` for slow steps  
**Command not found**: Check command exists in PATH  
**Working directory**: Ensure source is checked out to `working_directory`

## 📝 Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `GITHUB_TOKEN` | GitHub PAT with repo/checks/PR scopes | ✅ | - |
| `GITHUB_API_URL` | GitHub API base URL | ❌ | `https://api.github.com` |
| `SONAR_URL` | SonarQube server URL | ❌ | - |
| `SONAR_TOKEN` | SonarQube auth token | ❌ | - |
| `SONAR_USERNAME` | SonarQube username (alt auth) | ❌ | - |
| `SONAR_PASSWORD` | SonarQube password (alt auth) | ❌ | - |

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

## 🗺️ Roadmap

- [ ] GitLab and Bitbucket support
- [ ] Parallel file content fetching
- [ ] Caching layer for repeated API calls
- [ ] Metrics and telemetry
- [ ] Docker containerization
- [ ] Additional static analysis tools (ESLint, Checkstyle)
- [ ] Multi-language support (Python, Java, Go)
