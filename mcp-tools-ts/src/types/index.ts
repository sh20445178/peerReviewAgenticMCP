/**
 * Shared TypeScript types for the Peer Review MCP Tool Layer.
 */

// ── GitHub ─────────────────────────────────────────────────────────────────

export interface PRFile {
  filename: string;
  status: "added" | "removed" | "modified" | "renamed" | "copied" | "changed" | "unchanged";
  additions: number;
  deletions: number;
  changes: number;
  patch?: string;
  blob_url: string;
  raw_url: string;
  contents_url: string;
  previous_filename?: string;
}

export interface PRDetails {
  number: number;
  title: string;
  body: string | null;
  state: string;
  draft: boolean;
  author: string;
  headBranch: string;
  headSha: string;
  baseBranch: string;
  baseSha: string;
  htmlUrl: string;
  diffUrl: string;
  labels: string[];
  requestedReviewers: string[];
  additions: number;
  deletions: number;
  changedFiles: number;
  createdAt: string;
  updatedAt: string;
}

export interface PRChanges {
  pr: PRDetails;
  files: PRFile[];
}

export interface FileContent {
  repository: string;
  path: string;
  ref: string;
  content: string;
  encoding: string;
  size: number;
  sha: string;
}

export interface ReviewComment {
  body: string;
  path: string;
  line: number;
  side?: "LEFT" | "RIGHT";
  startLine?: number;
  startSide?: "LEFT" | "RIGHT";
}

export interface ReviewSubmission {
  body: string;
  event: "APPROVE" | "REQUEST_CHANGES" | "COMMENT";
  comments: ReviewComment[];
}

export interface CheckRunResult {
  checkRunId: number;
  name: string;
  status: "queued" | "in_progress" | "completed";
  conclusion: "success" | "failure" | "neutral" | "cancelled" | "skipped" | "timed_out" | "action_required" | null;
  title: string;
  summary: string;
  annotations: CheckAnnotation[];
}

export interface CheckAnnotation {
  path: string;
  startLine: number;
  endLine: number;
  annotationLevel: "notice" | "warning" | "failure";
  message: string;
  title?: string;
  rawDetails?: string;
}

// ── SonarQube ──────────────────────────────────────────────────────────────

export interface SonarIssue {
  key: string;
  rule: string;
  severity: "BLOCKER" | "CRITICAL" | "MAJOR" | "MINOR" | "INFO";
  component: string;
  line?: number;
  message: string;
  type: "BUG" | "VULNERABILITY" | "CODE_SMELL" | "SECURITY_HOTSPOT";
  effort?: string;
  debt?: string;
  tags: string[];
}

export interface SonarAnalysisResult {
  projectKey: string;
  taskId?: string;
  status: "SUCCESS" | "FAILED" | "IN_PROGRESS" | "PENDING";
  qualityGatePassed: boolean;
  qualityGateStatus: string;
  metrics: {
    bugs: number;
    vulnerabilities: number;
    codeSmells: number;
    coverage: number;
    duplications: number;
    linesOfCode: number;
    technicalDebt: string;
    securityHotspots: number;
    reliabilityRating: string;
    securityRating: string;
    maintainabilityRating: string;
  };
  issues: SonarIssue[];
  analysedAt: string;
}

// ── Build Validation ───────────────────────────────────────────────────────

export interface BuildStep {
  name: string;
  command: string;
  exitCode: number;
  stdout: string;
  stderr: string;
  durationMs: number;
}

export interface BuildResult {
  repository: string;
  ref: string;
  passed: boolean;
  steps: BuildStep[];
  totalDurationMs: number;
  startedAt: string;
  completedAt: string;
  error?: string;
}

// ── Code Suggestions ───────────────────────────────────────────────────────

export interface CodeSuggestion {
  file: string;
  startLine: number;
  endLine: number;
  originalCode: string;
  suggestedCode: string;
  rationale: string;
  category: "bug" | "security" | "performance" | "style" | "maintainability";
  severity: "critical" | "high" | "medium" | "low" | "info";
}

export interface SuggestionResult {
  repository: string;
  prNumber: number;
  totalSuggestions: number;
  suggestions: CodeSuggestion[];
  generatedAt: string;
}

// ── Governance ─────────────────────────────────────────────────────────────

export interface GovernanceReport {
  repository: string;
  prNumber: number;
  mergedAt: string;
  mergedBy: string;
  targetBranch: string;
  reviewers: string[];
  approvals: number;
  complianceScore: number;
  checks: GovernanceCheck[];
  sonarSummary?: {
    qualityGatePassed: boolean;
    bugs: number;
    vulnerabilities: number;
    coverage: number;
  };
  buildPassed: boolean;
  reportGeneratedAt: string;
}

export interface GovernanceCheck {
  name: string;
  passed: boolean;
  details: string;
  weight: number;
}

// ── Tool Input/Output schemas ──────────────────────────────────────────────

export interface ToolError {
  code: string;
  message: string;
  details?: unknown;
}
