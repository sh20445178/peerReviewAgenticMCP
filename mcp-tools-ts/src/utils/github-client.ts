/**
 * Shared GitHub REST API client built on @octokit/rest.
 */

import { Octokit } from "@octokit/rest";

let _client: Octokit | null = null;

export function getGitHubClient(): Octokit {
  if (!_client) {
    const token = process.env.GITHUB_TOKEN ?? process.env.GITHUB_ACCESS_TOKEN;
    if (!token) {
      throw new Error(
        "GitHub token not found. Set GITHUB_TOKEN or GITHUB_ACCESS_TOKEN environment variable."
      );
    }
    const baseUrl =
      process.env.GITHUB_API_URL ?? "https://api.github.com";

    _client = new Octokit({ auth: token, baseUrl });
  }
  return _client;
}

/** Split "owner/repo" into { owner, repo } */
export function parseRepo(repository: string): { owner: string; repo: string } {
  const parts = repository.split("/");
  if (parts.length !== 2 || !parts[0] || !parts[1]) {
    throw new Error(
      `Invalid repository format "${repository}". Expected "owner/repo".`
    );
  }
  return { owner: parts[0], repo: parts[1] };
}
