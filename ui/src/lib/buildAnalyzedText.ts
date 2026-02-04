import type { AnalyzeRequest } from "../api/types";

export function buildAnalyzedText(input: AnalyzeRequest): string {
  const parts: string[] = [];

  if (input.subject) parts.push(`Subject: ${input.subject}`);
  if (input.from_email) parts.push(`From: ${input.from_email}`);
  if (input.reply_to) parts.push(`Reply-To: ${input.reply_to}`);

  if (input.headers_raw) {
    parts.push("Headers:");
    parts.push(input.headers_raw);
  }

  if (input.body) {
    parts.push("Body:");
    parts.push(input.body);
  }

  if (input.attachments && input.attachments.length > 0) {
    parts.push("Attachments:");
    for (const a of input.attachments) {
      if (a?.filename) parts.push(`- ${a.filename}`);
    }
  }

  return parts.join("\n").trim();
}
