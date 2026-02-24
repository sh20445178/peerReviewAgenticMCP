/**
 * Tool 7 – Update GitHub Checks API
 *
 * Creates or updates a GitHub Check Run with pass/fail conclusion
 * and annotates individual file lines with findings.
 */

import { z } from "zod";
import type { CheckRunResult, CheckAnnotation } from "../types/index.js";
import { getGitHubClient, parseRepo } from "../utils/github-client.js";

// ── Input schema ────────────────────────────────────────────────────────────

const AnnotationSchema = z.object({
  path: z.string().describe("File path relative to the repository root."),
  start_line: z.number().int().positive(),
  end_line: z.number().int().positive(),
  annotation_level: z
    .enum(["notice", "warning", "failure"])
    .describe("Severity of the annotation."),
  message: z.string().describe("Description of the issue."),
  title: z.string().optional(),
  raw_details: z.string().optional(),
});

export const UpdateCheckRunInputSchema = z.object({
  repository: z
    .string()
    .describe('Full repository name in "owner/repo" format.'),
  head_sha: z
    .string()
    .describe("The SHA of the commit being checked."),
  check_name: z
    .string()
    .describe('Descriptive name for the check, e.g. "Peer Review – SonarQube".'),
  status: z
    .enum(["queued", "in_progress", "completed"])
    .default("completed")
    .describe("Current status of the check run."),
  conclusion: z
    .enum([
      "success",
      "failure",
      "neutral",
      "cancelled",
      "skipped",
      "timed_out",
      "action_required",
    ])
    .optional()
    .describe("Final verdict when status is completed."),
  title: z
    .string()
    .describe("Short title displayed in the GitHub UI next to the check name."),
  summary: z
    .string()
    .describe("Markdown body shown in the check run details panel."),
  annotations: z
    .array(AnnotationSchema)
    .optional()
    .default([])
    .describe(
      "Up to 50 line-level annotations. Use multiple calls to push all annotations."
    ),
  check_run_id: z
    .number()
    .int()
    .optional()
    .describe("If provided, updates an existing check run instead of creating a new one."),
});

export type UpdateCheckRunInput = z.infer<typeof UpdateCheckRunInputSchema>;

// ── Tool definition ─────────────────────────────────────────────────────────

export const updateCheckRunTool = {
  name: "update_github_check",
  description:
    "Creates a new GitHub Check Run or updates an existing one with a " +
    "pass/fail conclusion and optional file annotations. Use this after " +
    "running static analysis or build validation to report results directly " +
    "in the GitHub PR checks UI.",

  inputSchema: {
    type: "object" as const,
    properties: {
      repository: { type: "string" },
      head_sha: { type: "string" },
      check_name: { type: "string" },
      status: { type: "string", enum: ["queued", "in_progress", "completed"] },
      conclusion: {
        type: "string",
        enum: [
          "success",
          "failure",
          "neutral",
          "cancelled",
          "skipped",
          "timed_out",
          "action_required",
        ],
      },
      title: { type: "string" },
      summary: { type: "string" },
      annotations: {
        type: "array",
        items: {
          type: "object",
          properties: {
            path: { type: "string" },
            start_line: { type: "number" },
            end_line: { type: "number" },
            annotation_level: { type: "string" },
            message: { type: "string" },
            title: { type: "string" },
            raw_details: { type: "string" },
          },
          required: ["path", "start_line", "end_line", "annotation_level", "message"],
        },
      },
      check_run_id: { type: "number" },
    },
    required: ["repository", "head_sha", "check_name", "title", "summary"],
  },
} as const;

// ── Handler ─────────────────────────────────────────────────────────────────

export async function updateCheckRun(
  input: UpdateCheckRunInput
): Promise<CheckRunResult> {
  const { owner, repo } = parseRepo(input.repository);
  const octokit = getGitHubClient();

  const annotations: CheckAnnotation[] = (input.annotations ?? []).map((a) => ({
    path: a.path,
    startLine: a.start_line,
    endLine: a.end_line,
    annotationLevel: a.annotation_level,
    message: a.message,
    title: a.title,
    rawDetails: a.raw_details,
  }));

  // GitHub accepts max 50 annotations per API call; take first batch here.
  const annotationBatch = (input.annotations ?? []).slice(0, 50).map((a) => ({
    path: a.path,
    start_line: a.start_line,
    end_line: a.end_line,
    annotation_level: a.annotation_level as "notice" | "warning" | "failure",
    message: a.message,
    title: a.title,
    raw_details: a.raw_details,
  }));

  let checkRunId: number;
  let checkName: string;
  let status: string;
  let conclusion: string | null | undefined;

  if (input.check_run_id) {
    // Update existing check run
    const { data } = await octokit.checks.update({
      owner,
      repo,
      check_run_id: input.check_run_id,
      status: input.status,
      conclusion: input.conclusion,
      output: {
        title: input.title,
        summary: input.summary,
        annotations: annotationBatch,
      },
      completed_at: input.status === "completed" ? new Date().toISOString() : undefined,
    });
    checkRunId = data.id;
    checkName = data.name;
    status = data.status;
    conclusion = data.conclusion;
  } else {
    // Create new check run
    const { data } = await octokit.checks.create({
      owner,
      repo,
      name: input.check_name,
      head_sha: input.head_sha,
      status: input.status,
      conclusion: input.conclusion,
      started_at: new Date().toISOString(),
      completed_at: input.status === "completed" ? new Date().toISOString() : undefined,
      output: {
        title: input.title,
        summary: input.summary,
        annotations: annotationBatch,
      },
    });
    checkRunId = data.id;
    checkName = data.name;
    status = data.status;
    conclusion = data.conclusion;
  }

  return {
    checkRunId,
    name: checkName,
    status: status as CheckRunResult["status"],
    conclusion: (conclusion ?? null) as CheckRunResult["conclusion"],
    title: input.title,
    summary: input.summary,
    annotations,
  };
}
