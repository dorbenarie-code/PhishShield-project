import type { TextHighlight } from "../api/types";

export type TextSegment =
  | { kind: "text"; text: string }
  | { kind: "highlight"; text: string; highlight: TextHighlight };

function clamp(n: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, n));
}

function spanLen(h: TextHighlight): number {
  return h.end - h.start;
}

/**
 * Resolve overlaps by clustering intervals and picking ONE best highlight per cluster.
 * Preference: longest span; tie-breaker: earliest start.
 */
export function resolveHighlights(text: string, highlights: TextHighlight[]): TextHighlight[] {
  const maxLen = text.length;

  const cleaned = (highlights ?? [])
    .map((h) => ({
      ...h,
      start: clamp(Number(h.start), 0, maxLen),
      end: clamp(Number(h.end), 0, maxLen),
    }))
    .filter((h) => Number.isFinite(h.start) && Number.isFinite(h.end) && h.end > h.start && h.start < maxLen)
    .sort((a, b) => a.start - b.start || spanLen(b) - spanLen(a)); // start asc, longer first

  if (cleaned.length === 0) return [];

  const resolved: TextHighlight[] = [];

  let cluster: TextHighlight[] = [cleaned[0]];
  let clusterEnd = cleaned[0].end;

  const flush = () => {
    cluster.sort((a, b) => spanLen(b) - spanLen(a) || a.start - b.start);
    resolved.push(cluster[0]);
  };

  for (let i = 1; i < cleaned.length; i++) {
    const h = cleaned[i];
    if (h.start < clusterEnd) {
      cluster.push(h);
      clusterEnd = Math.max(clusterEnd, h.end);
    } else {
      flush();
      cluster = [h];
      clusterEnd = h.end;
    }
  }
  flush();

  return resolved.sort((a, b) => a.start - b.start || a.end - b.end);
}

export function toSegments(text: string, highlights: TextHighlight[]): TextSegment[] {
  const hs = resolveHighlights(text, highlights);
  const segments: TextSegment[] = [];

  let cursor = 0;
  for (const h of hs) {
    if (h.start > cursor) {
      segments.push({ kind: "text", text: text.slice(cursor, h.start) });
    }
    segments.push({
      kind: "highlight",
      text: text.slice(h.start, h.end),
      highlight: h,
    });
    cursor = h.end;
  }

  if (cursor < text.length) {
    segments.push({ kind: "text", text: text.slice(cursor) });
  }

  return segments;
}
