import type { TextHighlight } from "../api/types";
import { toSegments } from "../lib/highlightSegments";

type Props = {
  text: string;
  highlights: TextHighlight[];
};

export function HighlightedText({ text, highlights }: Props) {
  const segments = toSegments(text, highlights);

  return (
    <div className="panel">
      <div className="panel-header">
        <h3 className="panel-title small">Analyzed Text</h3>
        <div className="subtle">{text.length.toLocaleString()} chars</div>
      </div>

      <div className="text-view" role="region" aria-label="Analyzed text with highlights">
        {segments.map((seg, idx) => {
          if (seg.kind === "text") {
            return <span key={idx}>{seg.text}</span>;
          }

          const tip = `${seg.highlight.rule_id} — ${seg.highlight.label}`;
          return (
            <mark key={idx} className="hl" title={tip} data-rule-id={seg.highlight.rule_id}>
              {seg.text}
            </mark>
          );
        })}
      </div>

      <div className="hint subtle">Hover על ההדגשה כדי לראות איזה Rule תפס.</div>
    </div>
  );
}
