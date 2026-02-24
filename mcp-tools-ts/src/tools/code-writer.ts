/**
 * Tool 5 – Write Suggested Code Changes
 *
 * Accepts a list of structured code suggestions and applies them as
 * PR review comments with GitHub's "suggestion" fenced code block syntax.
 * Suggestions can be accepted directly by PR authors via the GitHub UI.
 */

import { z } from "zod";
import type { SuggestionResult, CodeSuggestion } from "../types/index.js";
import { getGitHubClient, parseRepo } from "../utils/github-client.js";

// ── Input schema ────────────────────────────────────────────────────────────

const SuggestionInputSchema = z.object({
  file: z.string().describe("Repository-relative path to the file, e.g. src/app.ts."),
  start_line: z.number().int().positive().describe("First line of the code block to replace."),
  end_line: z.number().int().positive().describe("Last line of the code block to replace."),
  original_code: z.string().describe("Exact original source lines being replaced."),
  suggested_code: z.string().describe("Replacement code to suggest."),
  rationale: z.string().describe("Explanation of why this change is recommended."),
  category: z
    .enum(["bug", "security", "performance", "style", "maintainability"])
    .describe("Type of improvement."),
  severity: z
    .enum(["critical", "high", "medium", "low", "info"])
    .describe("Urgency/importance of the suggestion."),
});

export const WriteCodeSuggestionsInputSchema = z.object({
  repository: z
    .string()
    .describe('Full repository name in "owner/repo" format.'),
  pr_number: z.number().int().positive().describe("Pull request number."),
  commit_id: z
    .string()
    .describe("The SHA of the HEAD commit to attach suggestions to."),
  suggestions: z
    .array(SuggestionInputSchema)
    .min(1)
    .describe("List of code suggestions to post as PR review comments."),
  post_as_review: z
    .boolean()
    .optional()
    .default(true)
    .describe(
      "When true, all suggestions are batched into a single review submission. " +
      "When false, each suggestion is posted as an individual comment."
    ),
  review_body: z
    .string()
    .optional()
    .default("")
    .describe("Optional top-level text body for the review (used when post_as_review=true)."),
});

export type WriteCodeSuggestionsInput = z.infer<typeof WriteCodeSuggestionsInputSchema>;

// ── Tool definition ─────────────────────────────────────────────────────────

export const writeCodeSuggestionsTool = {
  name: "write_code_suggestions",
  description:
    "Posts structured code improvement suggestions directly onto a GitHub PR " +
    "as review comments using GitHub's suggestion syntax. Each suggestion can " +
    "be accepted by the PR author with a single click. Covers bugs, security " +
    "issues, performance, style, and maintainability improvements.",

  inputSchema: {
    type: "object" as const,
    properties: {
      repository: { type: "string" },
      pr_number: { type: "number" },
      commit_id: { type: "string" },
      suggestions: {
        type: "array",
        items: {
          type: "object",
          properties: {
            file: { type: "string" },
            start_line: { type: "number" },
            end_line: { type: "number" },
            original_code: { type: "string" },
            suggested_code: { type: "string" },
            rationale: { type: "string" },
            category: { type: "string" },
            severity: { type: "string" },
          },
          required: ["file", "start_line", "end_line", "suggested_code", "rationale", "category", "severity"],
        },
        minItems: 1,
      },
      post_as_review: { type: "boolean" },
      review_body: { type: "string" },
    },
    required: ["repository", "pr_number", "commit_id", "suggestions"],
  },
} as const;

// ── Helpers ─────────────────────────────────────────────────────────────────

function buildCommentBody(s: z.infer<typeof SuggestionInputSchema>): string {
  const severityEmoji: Record<string, string> = {
    critical: "🔴",
    high: "🟠",
    medium: "🟡",
    low: "🔵",
    info: "⚪",
  };
  const emoji = severityEmoji[s.severity] ?? "⚪";
  return (
    `${emoji} **[${s.category.toUpperCase()} – ${s.severity}]** ${s.rationale}\n\n` +
    "```suggestion\n" +
    s.suggested_code +
    "\n```"
  );
}

// ── Handler ─────────────────────────────────────────────────────────────────

export async function writeCodeSuggestions(
  input: WriteCodeSuggestionsInput
): Promise<SuggestionResult> {
  const { owner, repo } = parseRepo(input.repository);
  const octokit = getGitHubClient();

  const mapped: CodeSuggestion[] = input.suggestions.map((s) => ({
    file: s.file,
    startLine: s.start_line,
    endLine: s.end_line,
    originalCode: s.original_code ?? "",
    suggestedCode: s.suggested_code,
    rationale: s.rationale,
    category: s.category,
    severity: s.severity,
  }));

  if (input.post_as_review ?? true) {
    // Batch all suggestions into a single review
    const reviewComments = input.suggestions.map((s) => {
      const body = buildCommentBody(s);
      if (s.start_line !== s.end_line) {
        return {
          path: s.file,
          start_line: s.start_line,
          line: s.end_line,
          side: "RIGHT" as const,
          start_side: "RIGHT" as const,
          body,
        };
      }
      return { path: s.file, line: s.end_line, side: "RIGHT" as const, body };
    });

    await octokit.pulls.createReview({
      owner,
      repo,
      pull_number: input.pr_number,
      commit_id: input.commit_id,
      body: input.review_body ?? "",
      event: "COMMENT",
      comments: reviewComments,
    });
  } else {
    // Post each suggestion as an individual review comment
    for (const s of input.suggestions) {
      const body = buildCommentBody(s);
      const params: Parameters<typeof octokit.pulls.createReviewComment>[0] = {
        owner,
        repo,
        pull_number: input.pr_number,
        commit_id: input.commit_id,
        path: s.file,
        line: s.end_line,
        side: "RIGHT",
        body,
      };
      if (s.start_line !== s.end_line) {
        params.start_line = s.start_line;
        params.start_side = "RIGHT";
      }
      await octokit.pulls.createReviewComment(params);
    }
  }

  return {
    repository: input.repository,
    prNumber: input.pr_number,
    totalSuggestions: mapped.length,
    suggestions: mapped,
    generatedAt: new Date().toISOString(),
  };
}
