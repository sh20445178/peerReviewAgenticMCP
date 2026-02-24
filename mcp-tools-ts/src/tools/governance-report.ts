/**
 * Tool 8 – Generate Post-Merge Governance Report
 *
 * After a PR is merged, fetches review history, approval counts, check
 * statuses, and SonarQube quality metrics then compiles them into a
 * structured governance compliance report.
 */

import { z } from "zod";
import type { GovernanceReport, GovernanceCheck } from "../types/index.js";
import { getGitHubClient, parseRepo } from "../utils/github-client.js";
import { getSonarClient } from "../utils/sonar-client.js";

// ── Input schema ────────────────────────────────────────────────────────────

export const GenerateGovernanceReportInputSchema = z.object({
  repository: z
    .string()
    .describe('Full repository name in "owner/repo" format.'),
  pr_number: z.number().int().positive().describe("Merged pull request number."),
  sonar_project_key: z
    .string()
    .optional()
    .describe(
      "SonarQube project key to include quality gate results in the report. " +
      "Omit if SonarQube is not configured."
    ),
  required_approvals: z
    .number()
    .int()
    .nonnegative()
    .optional()
    .default(1)
    .describe("Minimum number of approvals required for governance compliance."),
  required_checks: z
    .array(z.string())
    .optional()
    .default([])
    .describe("Names of GitHub status checks that must have passed."),
});

export type GenerateGovernanceReportInput = z.infer<
  typeof GenerateGovernanceReportInputSchema
>;

// ── Tool definition ─────────────────────────────────────────────────────────

export const generateGovernanceReportTool = {
  name: "generate_governance_report",
  description:
    "Generates a post-merge governance compliance report for a pull request. " +
    "Collects GitHub review approvals, check run statuses, merge details, and " +
    "optionally SonarQube quality gate results. Outputs a scored compliance " +
    "report that can be stored for audit purposes.",

  inputSchema: {
    type: "object" as const,
    properties: {
      repository: { type: "string" },
      pr_number: { type: "number" },
      sonar_project_key: { type: "string" },
      required_approvals: { type: "number" },
      required_checks: { type: "array", items: { type: "string" } },
    },
    required: ["repository", "pr_number"],
  },
} as const;

// ── Internal helpers ────────────────────────────────────────────────────────

interface Rating { label: string; value: string }

function ratingLabel(v?: string): string {
  const labels = ["", "A", "B", "C", "D", "E"];
  return labels[Number(v) | 0] ?? v ?? "N/A";
}

async function fetchSonarSummary(
  projectKey: string,
  branch?: string
): Promise<GovernanceReport["sonarSummary"]> {
  try {
    const client = getSonarClient();
    const params: Record<string, string> = { projectKey };
    if (branch) params["branch"] = branch;

    const [qgResp, metricsResp] = await Promise.all([
      client.get<{ projectStatus: { status: string } }>(
        "/qualitygates/project_status",
        { params }
      ),
      client.get<{
        component: { measures: Array<{ metric: string; value: string }> };
      }>("/measures/component", {
        params: {
          component: projectKey,
          metricKeys: "bugs,vulnerabilities,coverage",
          ...(branch ? { branch } : {}),
        },
      }),
    ]);

    const m = Object.fromEntries(
      metricsResp.data.component.measures.map((x) => [x.metric, x.value])
    );
    const qgStatus = qgResp.data.projectStatus.status;

    return {
      qualityGatePassed: qgStatus === "OK" || qgStatus === "NONE",
      bugs: Number(m["bugs"] ?? 0),
      vulnerabilities: Number(m["vulnerabilities"] ?? 0),
      coverage: parseFloat(m["coverage"] ?? "0"),
    };
  } catch {
    return undefined;
  }
}

// ── Handler ─────────────────────────────────────────────────────────────────

export async function generateGovernanceReport(
  input: GenerateGovernanceReportInput
): Promise<GovernanceReport> {
  const { owner, repo } = parseRepo(input.repository);
  const octokit = getGitHubClient();

  // Fetch PR details
  const { data: pr } = await octokit.pulls.get({
    owner,
    repo,
    pull_number: input.pr_number,
  });

  if (pr.state !== "closed" || !pr.merged_at) {
    throw new Error(
      `PR #${input.pr_number} has not been merged yet (state: ${pr.state}).`
    );
  }

  // Fetch reviews
  const reviews = await octokit.paginate(octokit.pulls.listReviews, {
    owner,
    repo,
    pull_number: input.pr_number,
    per_page: 100,
  });

  const approvals = reviews.filter((r) => r.state === "APPROVED");
  const uniqueApprovers = [...new Set(approvals.map((r) => r.user?.login ?? ""))].filter(Boolean);

  // Fetch check runs for the head SHA
  const { data: checksData } = await octokit.checks.listForRef({
    owner,
    repo,
    ref: pr.head.sha,
    per_page: 100,
  });

  const checkRuns = checksData.check_runs;

  // Governance checks
  const checks: GovernanceCheck[] = [];

  // 1) Approval count check
  const approvalsRequired = input.required_approvals ?? 1;
  checks.push({
    name: "Minimum Approvals",
    passed: uniqueApprovers.length >= approvalsRequired,
    details: `${uniqueApprovers.length}/${approvalsRequired} approvals received (${uniqueApprovers.join(", ") || "none"}).`,
    weight: 30,
  });

  // 2) Required checks
  const requiredChecks = input.required_checks ?? [];
  if (requiredChecks.length > 0) {
    const passedCheckNames = new Set(
      checkRuns
        .filter((c) => c.conclusion === "success")
        .map((c) => c.name)
    );
    const allChecksPassed = requiredChecks.every((name) => passedCheckNames.has(name));
    const failedChecks = requiredChecks.filter((n) => !passedCheckNames.has(n));
    checks.push({
      name: "Required CI Checks",
      passed: allChecksPassed,
      details: allChecksPassed
        ? `All ${requiredChecks.length} required checks passed.`
        : `Failed/missing checks: ${failedChecks.join(", ")}.`,
      weight: 30,
    });
  }

  // 3) PR description completeness
  const hasDescription = (pr.body?.trim().length ?? 0) > 20;
  checks.push({
    name: "PR Description",
    passed: hasDescription,
    details: hasDescription
      ? "PR has a meaningful description."
      : "PR description is missing or too brief.",
    weight: 10,
  });

  // 4) Review comments addressed (no unresolved REQUEST_CHANGES)
  const unresolvedChangesRequests = reviews.filter(
    (r) => r.state === "CHANGES_REQUESTED"
  );
  const changesResolved = unresolvedChangesRequests.length === 0;
  checks.push({
    name: "No Pending Change Requests",
    passed: changesResolved,
    details: changesResolved
      ? "No unresolved change requests."
      : `${unresolvedChangesRequests.length} unresolved change request(s) remain.`,
    weight: 20,
  });

  // 5) Build checks passed
  const allChecksPassed =
    checkRuns.length === 0 ||
    checkRuns.every((c) => c.conclusion === "success" || c.conclusion === "neutral" || c.conclusion === "skipped");
  checks.push({
    name: "All CI Checks Passed",
    passed: allChecksPassed,
    details: allChecksPassed
      ? `All ${checkRuns.length} CI check(s) passed.`
      : `Some checks failed: ${checkRuns
          .filter((c) => c.conclusion === "failure")
          .map((c) => c.name)
          .join(", ")}.`,
    weight: 10,
  });

  // Compute compliance score (weighted average of passed checks)
  const totalWeight = checks.reduce((s, c) => s + c.weight, 0);
  const passedWeight = checks
    .filter((c) => c.passed)
    .reduce((s, c) => s + c.weight, 0);
  const complianceScore =
    totalWeight > 0 ? Math.round((passedWeight / totalWeight) * 100) : 0;

  // Fetch SonarQube summary (optional)
  let sonarSummary: GovernanceReport["sonarSummary"];
  if (input.sonar_project_key) {
    sonarSummary = await fetchSonarSummary(
      input.sonar_project_key,
      pr.base.ref
    );
  }

  return {
    repository: input.repository,
    prNumber: input.pr_number,
    mergedAt: pr.merged_at,
    mergedBy: pr.merged_by?.login ?? "unknown",
    targetBranch: pr.base.ref,
    reviewers: uniqueApprovers,
    approvals: uniqueApprovers.length,
    complianceScore,
    checks,
    sonarSummary,
    buildPassed: allChecksPassed,
    reportGeneratedAt: new Date().toISOString(),
  };
}
