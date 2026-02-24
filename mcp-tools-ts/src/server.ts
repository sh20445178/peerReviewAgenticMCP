/**
 * MCP Server – Peer Review Agentic Tool Layer (TypeScript)
 *
 * Registers all 8 peer-review tools with the MCP SDK and routes
 * tool calls to their respective handlers.
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  type Tool,
} from "@modelcontextprotocol/sdk/types.js";

// ── Tool descriptors ────────────────────────────────────────────────────────
import { readPRChangesTool, ReadPRChangesInputSchema, readPRChanges } from "./tools/pr-reader.js";
import { fetchFileContentTool, FetchFileContentInputSchema, fetchFileContent } from "./tools/file-content.js";
import { runSonarScannerTool, RunSonarScannerInputSchema, runSonarScanner } from "./tools/sonar-scanner.js";
import { validateBuildTool, ValidateBuildInputSchema, validateBuild } from "./tools/build-validator.js";
import { writeCodeSuggestionsTool, WriteCodeSuggestionsInputSchema, writeCodeSuggestions } from "./tools/code-writer.js";
import { postAIReviewTool, PostAIReviewInputSchema, postAIReview } from "./tools/ai-reviewer.js";
import { updateCheckRunTool, UpdateCheckRunInputSchema, updateCheckRun } from "./tools/github-checks.js";
import {
  generateGovernanceReportTool,
  GenerateGovernanceReportInputSchema,
  generateGovernanceReport,
} from "./tools/governance-report.js";

// ── Server bootstrap ────────────────────────────────────────────────────────

const server = new Server(
  {
    name: "peer-review-mcp-ts",
    version: "1.0.0",
  },
  {
    capabilities: { tools: {} },
  }
);

// All registered tools indexed by name
const TOOLS: Tool[] = [
  readPRChangesTool,
  fetchFileContentTool,
  runSonarScannerTool,
  validateBuildTool,
  writeCodeSuggestionsTool,
  postAIReviewTool,
  updateCheckRunTool,
  generateGovernanceReportTool,
] as unknown as Tool[];

// ── List tools handler ──────────────────────────────────────────────────────

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: TOOLS,
}));

// ── Call tool handler ───────────────────────────────────────────────────────

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: rawArgs } = request.params;
  const args = rawArgs ?? {};

  try {
    switch (name) {
      // 1. Read PR Changes
      case "read_pr_changes": {
        const input = ReadPRChangesInputSchema.parse(args);
        const result = await readPRChanges(input);
        return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
      }

      // 2. Fetch Full File Content
      case "fetch_file_content": {
        const input = FetchFileContentInputSchema.parse(args);
        const result = await fetchFileContent(input);
        return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
      }

      // 3. Run Sonar Scanner
      case "run_sonar_scanner": {
        const input = RunSonarScannerInputSchema.parse(args);
        const result = await runSonarScanner(input);
        return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
      }

      // 4. Validate Build
      case "validate_build": {
        const input = ValidateBuildInputSchema.parse(args);
        const result = await validateBuild(input);
        return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
      }

      // 5. Write Code Suggestions
      case "write_code_suggestions": {
        const input = WriteCodeSuggestionsInputSchema.parse(args);
        const result = await writeCodeSuggestions(input);
        return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
      }

      // 6. Post AI Review Comments
      case "post_ai_review_comments": {
        const input = PostAIReviewInputSchema.parse(args);
        const result = await postAIReview(input);
        return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
      }

      // 7. Update GitHub Check Run
      case "update_github_check": {
        const input = UpdateCheckRunInputSchema.parse(args);
        const result = await updateCheckRun(input);
        return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
      }

      // 8. Generate Governance Report
      case "generate_governance_report": {
        const input = GenerateGovernanceReportInputSchema.parse(args);
        const result = await generateGovernanceReport(input);
        return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
      }

      default:
        return {
          content: [{ type: "text", text: `Unknown tool: ${name}` }],
          isError: true,
        };
    }
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({ error: message }, null, 2),
        },
      ],
      isError: true,
    };
  }
});

// ── Main ────────────────────────────────────────────────────────────────────

export async function startServer(): Promise<void> {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("[peer-review-mcp-ts] Server running on stdio");
}
