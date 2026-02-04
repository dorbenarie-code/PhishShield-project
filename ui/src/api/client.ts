/**
 * API Client - handles communication with the PhishShield backend
 * 
 * In development: Uses Vite proxy (requests go to /analyze, /health, etc.)
 * In production: Uses VITE_API_BASE_URL env var (e.g., http://localhost:8000)
 */

import type { AnalyzeRequest, AnalyzeResponse, HealthResponse, RuleSummary } from "./types";

// Get API base URL from environment, strip trailing slashes
const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/+$/, "");

/**
 * Build full URL for API endpoint
 * - If API_BASE is set (production): returns "http://backend:8000/path"
 * - If API_BASE is empty (dev): returns "/path" (handled by Vite proxy)
 */
function apiUrl(path: string): string {
  return API_BASE ? `${API_BASE}${path}` : path;
}

async function readTextSafe(res: Response): Promise<string> {
  try {
    return await res.text();
  } catch {
    return "";
  }
}

export async function checkHealth(): Promise<HealthResponse> {
  const res = await fetch(apiUrl("/health"));
  if (!res.ok) {
    throw new Error(`Health check failed: ${res.status} ${await readTextSafe(res)}`);
  }
  return res.json();
}

export async function analyzeEmail(request: AnalyzeRequest): Promise<AnalyzeResponse> {
  const res = await fetch(apiUrl("/analyze"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  if (!res.ok) {
    throw new Error(`Analysis failed: ${res.status} ${await readTextSafe(res)}`);
  }

  return res.json();
}

/**
 * Fetch loaded rule pack for Rule Pack Viewer
 */
export async function fetchRules(): Promise<RuleSummary[]> {
  const res = await fetch(apiUrl("/rules"));
  if (!res.ok) {
    throw new Error(`Rules fetch failed: ${res.status} ${await readTextSafe(res)}`);
  }
  return res.json();
}
