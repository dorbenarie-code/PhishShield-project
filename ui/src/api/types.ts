/**
 * API Types - mirrors the backend schemas
 */

export type Severity = "low" | "medium" | "high";
export type Action = "allow" | "verify_out_of_band" | "report" | "block";

export interface Evidence {
  kind: "keyword" | "regex";
  pattern: string;
  match: string;
  start: number;
  end: number;
  snippet: string;
  label?: string | null;
}

export interface RuleHit {
  rule_id: string;
  title: string;
  weight: number;
  severity: Severity;
  action: Action;
  explain: string;
  tags: string[];
  evidence: Evidence[];
}

export interface TextHighlight {
  start: number;
  end: number;
  rule_id: string;
  label: string;
}

export interface AnalyzeResponse {
  score: number;
  severity: Severity;
  action: Action;
  recommendations: string[];
  hits: RuleHit[];
  highlights: TextHighlight[];
}

export interface AttachmentMeta {
  filename: string;
  size_bytes?: number | null;
}

export interface AnalyzeRequest {
  subject: string;
  body: string;
  from_email: string | null;
  reply_to: string | null;
  headers_raw: string;
  attachments: AttachmentMeta[];
}

export interface HealthResponse {
  status: string;
}

/**
 * Rule summary for Rule Pack Viewer
 * Returned by GET /rules endpoint
 */
export interface RuleSummary {
  id: string;
  title: string;
  weight: number;
  severity: Severity;
  tags: string[];
}
