/**
 * Thin SonarQube REST API client using axios.
 */

import axios, { type AxiosInstance } from "axios";

let _client: AxiosInstance | null = null;

export function getSonarClient(): AxiosInstance {
  if (!_client) {
    const url = process.env.SONAR_URL ?? process.env.SONARQUBE_URL;
    if (!url) {
      throw new Error(
        "SonarQube URL not found. Set SONAR_URL or SONARQUBE_URL environment variable."
      );
    }

    const token = process.env.SONAR_TOKEN ?? process.env.SONARQUBE_TOKEN;
    const username = process.env.SONAR_USERNAME;
    const password = process.env.SONAR_PASSWORD;

    const auth =
      token
        ? { username: token, password: "" }
        : username && password
          ? { username, password }
          : undefined;

    _client = axios.create({
      baseURL: url.replace(/\/$/, "") + "/api",
      auth,
      timeout: 30_000,
      headers: { "Content-Type": "application/json" },
    });
  }
  return _client;
}
