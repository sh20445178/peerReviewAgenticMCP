/**
 * Tool 1 – Read PR Changes
 *
 * Reads pull-request metadata and the full list of changed files
 * (including diffs/patches) via the GitHub REST API.
 */

import { z } from "zod";
import type { PRChanges, PRFile } from "../types/index.js";
import { getGitHubClient, parseRepo } from "../utils/github-client.js";

// ── Input schema ────────────────────────────────────────────────────────────

export const ReadPRChangesInputSchema = z.object({
  repository: z
    .string()
    .describe('Full repository name in "owner/repo" format.'),
  pr_number: z
    .number()
    .int()
    .positive()
    .describe("Pull request number."),
  include_patch: z
    .boolean()
    .optional()
    .default(true)
    .describe("Whether to include the raw unified diff patch for each file."),
});

export type ReadPRChangesInput = z.infer<typeof ReadPRChangesInputSchema>;

// ── Tool definition (MCP descriptor) ───────────────────────────────────────

export const readPRChangesTool = {
  name: "read_pr_changes",
  description:
    "Reads pull request metadata and the full list of changed files " +
    "(additions, deletions, patches) from GitHub using the REST API. " +
    "Use this as the first step of any PR review workflow.",

  inputSchema: {
    type: "object" as const,
    properties: {
      repository: {
        type: "string",
        description: 'Full repository name in "owner/repo" format.',
      },
      pr_number: {
        type: "number",
        description: "Pull request number.",
      },
      include_patch: {
        type: "boolean",
        description: "Whether to include the raw unified diff patch per file. Defaults to true.",
      },
    },
    required: ["repository", "pr_number"],
  },
} as const;

// ── Handler ─────────────────────────────────────────────────────────────────

export async function readPRChanges(input: ReadPRChangesInput): Promise<PRChanges> {
  const { owner, repo } = parseRepo(input.repository);
  const octokit = getGitHubClient();

  // Fetch PR metadata
  const { data: pr } = await octokit.pulls.get({
    owner,
    repo,
    pull_number: input.pr_number,
  });

  // Fetch changed files (paginated – GitHub caps at 300 files per PR)
  const filesData = await octokit.paginate(octokit.pulls.listFiles, {
    owner,
    repo,
    pull_number: input.pr_number,
    per_page: 100,
  });

  const files: PRFile[] = filesData.map((f) => ({
    filename: f.filename,
    status: f.status as PRFile["status"],
    additions: f.additions,
    deletions: f.deletions,
    changes: f.changes,
    patch: input.include_patch ? f.patch : undefined,
    blob_url: f.blob_url,
    raw_url: f.raw_url,
    contents_url: f.contents_url,
    previous_filename: f.previous_filename,
  }));

  return {
    pr: {
      number: pr.number,
      title: pr.title,
      body: pr.body ?? null,
      state: pr.state,
      draft: pr.draft ?? false,
      author: pr.user?.login ?? "unknown",
      headBranch: pr.head.ref,
      headSha: pr.head.sha,
      baseBranch: pr.base.ref,
      baseSha: pr.base.sha,
      htmlUrl: pr.html_url,
      diffUrl: pr.diff_url ?? "",
      labels: pr.labels.map((l) => l.name ?? ""),
      requestedReviewers: pr.requested_reviewers?.map((r) => r.login) ?? [],
      additions: pr.additions,
      deletions: pr.deletions,
      changedFiles: pr.changed_files,
      createdAt: pr.created_at,
      updatedAt: pr.updated_at,
    },
    files,
  };
}
