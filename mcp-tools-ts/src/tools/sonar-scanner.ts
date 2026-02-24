/**
 * Tool 3 – Run Static Analysis via SonarQube Scanner
 *
 * Triggers a SonarScanner analysis for a given project key and branch,
 * polls for the task to complete, then returns quality gate status,
 * metrics, and a paginated list of issues.
 */

import { z } from "zod";
import type { SonarAnalysisResult, SonarIssue } from "../types/index.js";
import { getSonarClient } from "../utils/sonar-client.js";
import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

// ── Input schema ────────────────────────────────────────────────────────────

export const RunSonarScannerInputSchema = z.object({
  project_key: z
    .string()
    .describe("SonarQube project key, e.g. org.example:my-service"),
  project_base_dir: z
    .string()
    .describe("Absolute path to the checked-out source directory to scan."),
  branch: z
    .string()
    .optional()
    .describe("Branch name to associate the analysis with in SonarQube."),
  pr_key: z
    .string()
    .optional()
    .describe("Pull-request key (number as string) for PR-decoration mode."),
  pr_branch: z
    .string()
    .optional()
    .describe("Source branch of the PR (required when pr_key is set)."),
  pr_base: z
    .string()
    .optional()
    .describe("Target branch of the PR (required when pr_key is set)."),
  extra_properties: z
    .record(z.string())
    .optional()
    .describe("Additional sonar.* properties to pass to the scanner."),
  poll_timeout_seconds: z
    .number()
    .int()
    .positive()
    .optional()
    .default(300)
    .describe("Max seconds to wait for the analysis task to finish."),
});

export type RunSonarScannerInput = z.infer<typeof RunSonarScannerInputSchema>;

// ── Tool definition ─────────────────────────────────────────────────────────

export const runSonarScannerTool = {
  name: "run_sonar_scanner",
  description:
    "Runs the SonarScanner CLI against a local source directory, waits for " +
    "the background analysis task to complete, then returns the quality gate " +
    "status, key metrics (bugs, vulnerabilities, coverage, duplication), and " +
    "the full list of new issues found in this analysis.",

  inputSchema: {
    type: "object" as const,
    properties: {
      project_key: { type: "string" },
      project_base_dir: { type: "string" },
      branch: { type: "string" },
      pr_key: { type: "string" },
      pr_branch: { type: "string" },
      pr_base: { type: "string" },
      extra_properties: { type: "object", additionalProperties: { type: "string" } },
      poll_timeout_seconds: { type: "number" },
    },
    required: ["project_key", "project_base_dir"],
  },
} as const;

// ── Internal helpers ────────────────────────────────────────────────────────

async function waitForTask(taskId: string, timeoutMs: number): Promise<void> {
  const client = getSonarClient();
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const resp = await client.get<{ task: { status: string } }>(
      "/ce/task",
      { params: { id: taskId } }
    );
    const { status } = resp.data.task;
    if (status === "SUCCESS") return;
    if (status === "FAILED" || status === "CANCELLED") {
      throw new Error(`SonarQube analysis task ${taskId} ended with status: ${status}`);
    }
    await new Promise((r) => setTimeout(r, 5_000));
  }
  throw new Error("Timed out waiting for SonarQube analysis task to complete.");
}

async function fetchMetrics(projectKey: string, branch?: string): Promise<SonarAnalysisResult["metrics"]> {
  const client = getSonarClient();
  const metricKeys = [
    "bugs",
    "vulnerabilities",
    "code_smells",
    "coverage",
    "duplicated_lines_density",
    "ncloc",
    "sqale_index",
    "security_hotspots",
    "reliability_rating",
    "security_rating",
    "sqale_rating",
  ].join(",");

  const params: Record<string, string> = {
    component: projectKey,
    metricKeys,
  };
  if (branch) params["branch"] = branch;

  const resp = await client.get<{
    component: { measures: Array<{ metric: string; value: string }> };
  }>("/measures/component", { params });

  const m = Object.fromEntries(
    resp.data.component.measures.map((x) => [x.metric, x.value])
  );

  const ratingLabel = (v?: string) => {
    const ratings = ["", "A", "B", "C", "D", "E"];
    return ratings[Number(v) | 0] ?? v ?? "N/A";
  };

  return {
    bugs: Number(m["bugs"] ?? 0),
    vulnerabilities: Number(m["vulnerabilities"] ?? 0),
    codeSmells: Number(m["code_smells"] ?? 0),
    coverage: parseFloat(m["coverage"] ?? "0"),
    duplications: parseFloat(m["duplicated_lines_density"] ?? "0"),
    linesOfCode: Number(m["ncloc"] ?? 0),
    technicalDebt: m["sqale_index"] ? `${m["sqale_index"]}min` : "0min",
    securityHotspots: Number(m["security_hotspots"] ?? 0),
    reliabilityRating: ratingLabel(m["reliability_rating"]),
    securityRating: ratingLabel(m["security_rating"]),
    maintainabilityRating: ratingLabel(m["sqale_rating"]),
  };
}

async function fetchIssues(projectKey: string, branch?: string): Promise<SonarIssue[]> {
  const client = getSonarClient();
  const issues: SonarIssue[] = [];
  let page = 1;
  const pageSize = 100;

  while (true) {
    const params: Record<string, string | number> = {
      componentKeys: projectKey,
      p: page,
      ps: pageSize,
      resolved: "false",
    };
    if (branch) params["branch"] = branch;

    const resp = await client.get<{
      issues: Array<{
        key: string;
        rule: string;
        severity: string;
        component: string;
        line?: number;
        message: string;
        type: string;
        effort?: string;
        debt?: string;
        tags: string[];
      }>;
      total: number;
    }>("/issues/search", { params });

    for (const i of resp.data.issues) {
      issues.push({
        key: i.key,
        rule: i.rule,
        severity: i.severity as SonarIssue["severity"],
        component: i.component,
        line: i.line,
        message: i.message,
        type: i.type as SonarIssue["type"],
        effort: i.effort,
        debt: i.debt,
        tags: i.tags ?? [],
      });
    }

    if (issues.length >= resp.data.total || resp.data.issues.length < pageSize) break;
    page++;
  }

  return issues;
}

// ── Handler ─────────────────────────────────────────────────────────────────

export async function runSonarScanner(
  input: RunSonarScannerInput
): Promise<SonarAnalysisResult> {
  const sonarUrl =
    process.env.SONAR_URL ?? process.env.SONARQUBE_URL ?? "http://localhost:9000";
  const sonarToken = process.env.SONAR_TOKEN ?? process.env.SONARQUBE_TOKEN ?? "";

  // Build sonar-scanner CLI arguments
  const args: string[] = [
    `-Dsonar.projectKey=${input.project_key}`,
    `-Dsonar.projectBaseDir=${input.project_base_dir}`,
    `-Dsonar.host.url=${sonarUrl}`,
    `-Dsonar.login=${sonarToken}`,
  ];

  if (input.branch) args.push(`-Dsonar.branch.name=${input.branch}`);
  if (input.pr_key) args.push(`-Dsonar.pullrequest.key=${input.pr_key}`);
  if (input.pr_branch) args.push(`-Dsonar.pullrequest.branch=${input.pr_branch}`);
  if (input.pr_base) args.push(`-Dsonar.pullrequest.base=${input.pr_base}`);

  for (const [k, v] of Object.entries(input.extra_properties ?? {})) {
    args.push(`-D${k}=${v}`);
  }

  // Run scanner
  const { stdout } = await execFileAsync("sonar-scanner", args, {
    cwd: input.project_base_dir,
    maxBuffer: 10 * 1024 * 1024,
  });

  // Extract task ID from scanner output
  const taskIdMatch = stdout.match(/task\?id=([a-zA-Z0-9_-]+)/);
  const taskId = taskIdMatch?.[1];

  if (taskId) {
    await waitForTask(taskId, (input.poll_timeout_seconds ?? 300) * 1000);
  }

  // Quality gate
  const client = getSonarClient();
  const qgParams: Record<string, string> = { projectKey: input.project_key };
  if (input.pr_key) qgParams["pullRequest"] = input.pr_key;
  else if (input.branch) qgParams["branch"] = input.branch;

  const qgResp = await client.get<{
    projectStatus: { status: string };
  }>("/qualitygates/project_status", { params: qgParams });

  const qgStatus = qgResp.data.projectStatus.status;
  const qualityGatePassed = qgStatus === "OK" || qgStatus === "NONE";

  const [metrics, issues] = await Promise.all([
    fetchMetrics(input.project_key, input.branch),
    fetchIssues(input.project_key, input.branch),
  ]);

  return {
    projectKey: input.project_key,
    taskId,
    status: "SUCCESS",
    qualityGatePassed,
    qualityGateStatus: qgStatus,
    metrics,
    issues,
    analysedAt: new Date().toISOString(),
  };
}
