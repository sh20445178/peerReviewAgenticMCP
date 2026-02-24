#!/usr/bin/env node
/**
 * Entry point for the Peer Review MCP TypeScript tool layer.
 * Loads environment variables then starts the MCP server on stdio.
 */

import "dotenv/config";
import { startServer } from "./server.js";

startServer().catch((err: unknown) => {
  console.error("[peer-review-mcp-ts] Fatal error:", err);
  process.exit(1);
});
