/**
 * Tool 2 – Fetch Full File Content
 *
 * Retrieves the complete content of a file at a specific git ref
 * for thorough deep review (not just the patch/diff).
 */

import { z } from "zod";
import type { FileContent } from "../types/index.js";
import { getGitHubClient, parseRepo } from "../utils/github-client.js";

// ── Input schema ────────────────────────────────────────────────────────────

export const FetchFileContentInputSchema = z.object({
  repository: z
    .string()
    .describe('Full repository name in "owner/repo" format.'),
  path: z
    .string()
    .describe('Path to the file inside the repository, e.g. "src/app.ts".'),
  ref: z
    .string()
    .optional()
    .describe(
      "Git ref (branch, tag, or commit SHA) to read. Defaults to the repository default branch."
    ),
});

export type FetchFileContentInput = z.infer<typeof FetchFileContentInputSchema>;

// ── Tool definition ─────────────────────────────────────────────────────────

export const fetchFileContentTool = {
  name: "fetch_file_content",
  description:
    "Fetches the full source code of a file from a GitHub repository at a " +
    "given commit / branch ref. Returns decoded UTF-8 content suitable for " +
    "in-depth AI code review. Pair with read_pr_changes to review each " +
    "changed file in full context.",

  inputSchema: {
    type: "object" as const,
    properties: {
      repository: {
        type: "string",
        description: 'Full repository name in "owner/repo" format.',
      },
      path: {
        type: "string",
        description: 'File path inside the repository, e.g. "src/app.ts".',
      },
      ref: {
        type: "string",
        description:
          "Git ref (branch, tag, SHA). Defaults to the repository default branch.",
      },
    },
    required: ["repository", "path"],
  },
} as const;

// ── Handler ─────────────────────────────────────────────────────────────────

export async function fetchFileContent(
  input: FetchFileContentInput
): Promise<FileContent> {
  const { owner, repo } = parseRepo(input.repository);
  const octokit = getGitHubClient();

  const params: Parameters<typeof octokit.repos.getContent>[0] = {
    owner,
    repo,
    path: input.path,
  };
  if (input.ref) params.ref = input.ref;

  const { data } = await octokit.repos.getContent(params);

  // GitHub returns an array for directory listings; we only accept files.
  if (Array.isArray(data)) {
    throw new Error(
      `Path "${input.path}" points to a directory, not a file.`
    );
  }

  if (data.type !== "file") {
    throw new Error(
      `Path "${input.path}" is of type "${data.type}", not a file.`
    );
  }

  const fileData = data as {
    type: "file";
    content: string;
    encoding: string;
    size: number;
    sha: string;
    path: string;
  };

  // Decode Base-64 content returned by the GitHub API
  const rawContent = Buffer.from(
    fileData.content.replace(/\n/g, ""),
    fileData.encoding as BufferEncoding
  ).toString("utf-8");

  return {
    repository: input.repository,
    path: fileData.path,
    ref: input.ref ?? "default",
    content: rawContent,
    encoding: fileData.encoding,
    size: fileData.size,
    sha: fileData.sha,
  };
}
