/**
 * Tool 6 – Post AI Review Comments on a PR
 *
 * Accepts pre-generated AI review findings and posts them as a structured
 * GitHub pull-request review (APPROVE / REQUEST_CHANGES / COMMENT) with
 * optional inline comments on specific file lines.
 */

import { z } from "zod";
import type { ReviewSubmission } from "../types/index.js";
import { getGitHubClient, parseRepo } from "../utils/github-client.js";

// ── Input schema ────────────────────────────────────────────────────────────

const InlineCommentSchema = z.object({
  path: z.string().describe("Repository-relative file path."),
  line: z.number().int().positive().describe("Line number the comment targets."),
  body: z.string().describe("Markdown text of the inline comment."),
  side: z.enum(["LEFT", "RIGHT"]).optional().default("RIGHT"),
  start_line: z
    .number()
    .int()
    .positive()
    .optional()
    .describe("First line for a multi-line comment range."),
  start_side: z.enum(["LEFT", "RIGHT"]).optional(),
});

export const PostAIReviewInputSchema = z.object({
  repository: z
    .string()
    .describe('Full repository name in "owner/repo" format.'),
  pr_number: z.number().int().positive().describe("Pull request number."),
  commit_id: z
    .string()
    .describe("HEAD commit SHA of the PR branch to anchor the review to."),
  review_body: z
    .string()
    .describe(
      "Top-level review summary in Markdown. Summarise overall findings, " +
      "risk level, and a recommendation."
    ),
  verdict: z
    .enum(["APPROVE", "REQUEST_CHANGES", "COMMENT"])
    .describe(
      "Review verdict. Use APPROVE when the code is acceptable, " +
      "REQUEST_CHANGES when blocking issues exist, COMMENT for informational reviews."
    ),
  inline_comments: z
    .array(InlineCommentSchema)
    .optional()
    .default([])
    .describe("Optional list of line-level review comments to include in the review."),
});

export type PostAIReviewInput = z.infer<typeof PostAIReviewInputSchema>;

// ── Tool definition ─────────────────────────────────────────────────────────

export const postAIReviewTool = {
  name: "post_ai_review_comments",
  description:
    "Submits an AI-generated pull request review to GitHub. The review " +
    "includes a top-level summary and optional inline comments on specific " +
    "lines. The verdict can approve the PR, request changes, or leave an " +
    "informational comment. This tool is used after the AI agent analyses " +
    "the PR diff and file contents.",

  inputSchema: {
    type: "object" as const,
    properties: {
      repository: { type: "string" },
      pr_number: { type: "number" },
      commit_id: { type: "string" },
      review_body: { type: "string" },
      verdict: {
        type: "string",
        enum: ["APPROVE", "REQUEST_CHANGES", "COMMENT"],
      },
      inline_comments: {
        type: "array",
        items: {
          type: "object",
          properties: {
            path: { type: "string" },
            line: { type: "number" },
            body: { type: "string" },
            side: { type: "string", enum: ["LEFT", "RIGHT"] },
            start_line: { type: "number" },
            start_side: { type: "string", enum: ["LEFT", "RIGHT"] },
          },
          required: ["path", "line", "body"],
        },
      },
    },
    required: ["repository", "pr_number", "commit_id", "review_body", "verdict"],
  },
} as const;

// ── Handler ─────────────────────────────────────────────────────────────────

export async function postAIReview(input: PostAIReviewInput): Promise<{
  reviewId: number;
  state: string;
  htmlUrl: string;
  submission: ReviewSubmission;
}> {
  const { owner, repo } = parseRepo(input.repository);
  const octokit = getGitHubClient();

  const reviewComments = (input.inline_comments ?? []).map((c) => {
    const comment: {
      path: string;
      line: number;
      body: string;
      side: "LEFT" | "RIGHT";
      start_line?: number;
      start_side?: "LEFT" | "RIGHT";
    } = {
      path: c.path,
      line: c.line,
      body: c.body,
      side: (c.side ?? "RIGHT") as "LEFT" | "RIGHT",
    };
    if (c.start_line) {
      comment.start_line = c.start_line;
      comment.start_side = (c.start_side ?? "RIGHT") as "LEFT" | "RIGHT";
    }
    return comment;
  });

  const { data } = await octokit.pulls.createReview({
    owner,
    repo,
    pull_number: input.pr_number,
    commit_id: input.commit_id,
    body: input.review_body,
    event: input.verdict,
    comments: reviewComments,
  });

  const submission: ReviewSubmission = {
    body: input.review_body,
    event: input.verdict,
    comments: (input.inline_comments ?? []).map((c) => ({
      body: c.body,
      path: c.path,
      line: c.line,
      side: (c.side ?? "RIGHT") as "LEFT" | "RIGHT",
      startLine: c.start_line,
      startSide: c.start_side as "LEFT" | "RIGHT" | undefined,
    })),
  };

  return {
    reviewId: data.id,
    state: data.state,
    htmlUrl: data.html_url ?? "",
    submission,
  };
}
