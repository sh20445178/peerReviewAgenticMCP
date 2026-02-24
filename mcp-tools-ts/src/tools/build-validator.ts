/**
 * Tool 4 – Validate Source Code Build
 *
 * Runs a configurable sequence of build/test commands in a checked-out
 * source directory and reports per-step exit codes, stdout/stderr, and
 * overall pass/fail.
 */

import { z } from "zod";
import type { BuildResult, BuildStep } from "../types/index.js";
import { spawn } from "node:child_process";
import { performance } from "node:perf_hooks";

// ── Input schema ────────────────────────────────────────────────────────────

const BuildStepInputSchema = z.object({
  name: z.string().describe("Human-readable step label, e.g. 'Install dependencies'."),
  command: z.string().describe("Shell command to run, e.g. 'npm ci'."),
  continue_on_error: z
    .boolean()
    .optional()
    .default(false)
    .describe("When true, the pipeline continues even if this step fails."),
  timeout_seconds: z
    .number()
    .int()
    .positive()
    .optional()
    .default(300)
    .describe("Per-step timeout in seconds."),
  env: z
    .record(z.string())
    .optional()
    .describe("Extra environment variables to inject for this step."),
});

export const ValidateBuildInputSchema = z.object({
  repository: z
    .string()
    .describe("Repository identifier (used for result labelling only)."),
  ref: z
    .string()
    .describe("Git ref or commit SHA being validated (used for result labelling)."),
  working_directory: z
    .string()
    .describe("Absolute path to the checked-out source directory."),
  steps: z
    .array(BuildStepInputSchema)
    .min(1)
    .describe("Ordered sequence of build/test steps to run."),
  stop_on_first_failure: z
    .boolean()
    .optional()
    .default(true)
    .describe("Stop executing subsequent steps when a step fails."),
});

export type ValidateBuildInput = z.infer<typeof ValidateBuildInputSchema>;

// ── Tool definition ─────────────────────────────────────────────────────────

export const validateBuildTool = {
  name: "validate_build",
  description:
    "Runs an ordered list of build, lint, and test commands inside a local " +
    "source directory. Returns per-step stdout/stderr, exit codes, and an " +
    "overall pass/fail verdict. Designed to validate that a PR does not " +
    "break the build before merge.",

  inputSchema: {
    type: "object" as const,
    properties: {
      repository: { type: "string" },
      ref: { type: "string" },
      working_directory: { type: "string" },
      steps: {
        type: "array",
        items: {
          type: "object",
          properties: {
            name: { type: "string" },
            command: { type: "string" },
            continue_on_error: { type: "boolean" },
            timeout_seconds: { type: "number" },
            env: { type: "object", additionalProperties: { type: "string" } },
          },
          required: ["name", "command"],
        },
        minItems: 1,
      },
      stop_on_first_failure: { type: "boolean" },
    },
    required: ["repository", "ref", "working_directory", "steps"],
  },
} as const;

// ── Internal helper ─────────────────────────────────────────────────────────

function runCommand(
  command: string,
  cwd: string,
  env: NodeJS.ProcessEnv,
  timeoutMs: number
): Promise<{ exitCode: number; stdout: string; stderr: string }> {
  return new Promise((resolve) => {
    let stdout = "";
    let stderr = "";
    let settled = false;

    const child = spawn("sh", ["-c", command], {
      cwd,
      env,
      stdio: "pipe",
    });

    const timer = setTimeout(() => {
      if (!settled) {
        settled = true;
        child.kill("SIGTERM");
        resolve({
          exitCode: 124,
          stdout,
          stderr: stderr + "\n[TIMEOUT] Command exceeded time limit.",
        });
      }
    }, timeoutMs);

    child.stdout.on("data", (d: Buffer) => { stdout += d.toString(); });
    child.stderr.on("data", (d: Buffer) => { stderr += d.toString(); });

    child.on("close", (code) => {
      if (!settled) {
        settled = true;
        clearTimeout(timer);
        resolve({ exitCode: code ?? 1, stdout, stderr });
      }
    });

    child.on("error", (err) => {
      if (!settled) {
        settled = true;
        clearTimeout(timer);
        resolve({ exitCode: 1, stdout, stderr: stderr + "\n" + String(err) });
      }
    });
  });
}

// ── Handler ─────────────────────────────────────────────────────────────────

export async function validateBuild(input: ValidateBuildInput): Promise<BuildResult> {
  const startedAt = new Date().toISOString();
  const totalStart = performance.now();
  const completedSteps: BuildStep[] = [];
  let overallPassed = true;

  for (const step of input.steps) {
    const stepEnv: NodeJS.ProcessEnv = {
      ...process.env,
      ...(step.env ?? {}),
    };

    const t0 = performance.now();
    const result = await runCommand(
      step.command,
      input.working_directory,
      stepEnv,
      (step.timeout_seconds ?? 300) * 1000
    );
    const durationMs = Math.round(performance.now() - t0);

    const stepPassed = result.exitCode === 0;

    completedSteps.push({
      name: step.name,
      command: step.command,
      exitCode: result.exitCode,
      stdout: result.stdout,
      stderr: result.stderr,
      durationMs,
    });

    if (!stepPassed) {
      overallPassed = false;
      if (input.stop_on_first_failure && !step.continue_on_error) {
        break;
      }
    }
  }

  return {
    repository: input.repository,
    ref: input.ref,
    passed: overallPassed,
    steps: completedSteps,
    totalDurationMs: Math.round(performance.now() - totalStart),
    startedAt,
    completedAt: new Date().toISOString(),
  };
}
