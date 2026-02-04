/**
 * ResultsPanel - displays analysis results with SOC workflow actions
 */

import { useState } from "react";
import type { AnalyzeResponse } from "../api/types";
import { copyToClipboard } from "../lib/clipboard";
import { SeverityBadge } from "./SeverityBadge";

interface Props {
  result: AnalyzeResponse | null;
  error?: string | null;
  analyzedText?: string;
}

/**
 * CopyButton - reusable button with copy feedback
 */
function CopyButton({ label, text, variant = "secondary" }: { 
  label: string; 
  text: string;
  variant?: "primary" | "secondary";
}) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    const success = await copyToClipboard(text);
    if (success) {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    }
  }

  return (
    <button 
      className={`btn btn-${variant}`} 
      onClick={handleCopy} 
      type="button"
      title={`Copy ${label.toLowerCase()} to clipboard`}
    >
      {copied ? "✅ Copied!" : label}
    </button>
  );
}

/**
 * ResultActions - SOC workflow action buttons
 */
function ResultActions({
  result,
  analyzedText,
}: {
  result: AnalyzeResponse;
  analyzedText: string;
}) {
  return (
    <div className="action-row">
      <CopyButton label="📋 Copy JSON" text={JSON.stringify(result, null, 2)} />
      <CopyButton label="📝 Copy Text" text={analyzedText} />
    </div>
  );
}

export function ResultsPanel({ result, error, analyzedText }: Props) {
  // Show error if present
  if (error) {
    return (
      <div className="error-box">
        <strong>❌ Error:</strong> {error}
      </div>
    );
  }

  // Show placeholder if no result yet
  if (!result) {
    return (
      <div className="placeholder-box">
        <div style={{ fontSize: 48, marginBottom: 8, opacity: 0.5 }}>🔍</div>
        <div>Enter email details and click Analyze</div>
        <div className="subtle" style={{ marginTop: 8 }}>
          Results will appear here with risk score, triggered rules, and highlights
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      {/* Score Header */}
      <div className="score-header">
        <div
          className="score-value"
          style={{
            color: result.score >= 70 ? "#ef4444" : result.score >= 30 ? "#f59e0b" : "#22c55e",
          }}
        >
          {result.score}
        </div>
        <div className="score-details">
          <div style={{ marginBottom: 6 }}>
            <SeverityBadge severity={result.severity} size="lg" />
          </div>
          <div className="action-label">
            Action: <strong className={`action-${result.action}`}>{result.action}</strong>
          </div>
        </div>
      </div>

      {/* SOC Workflow Actions */}
      {analyzedText && <ResultActions result={result} analyzedText={analyzedText} />}

      {/* Recommendations */}
      {result.recommendations.length > 0 && (
        <div className="section">
          <h3 className="section-title">💡 Recommendations</h3>
          <ul className="recommendations-list">
            {result.recommendations.map((rec, i) => (
              <li key={i}>{rec}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Rule Hits */}
      {result.hits.length > 0 && (
        <div className="section">
          <h3 className="section-title">
            🎯 Triggered Rules ({result.hits.length})
          </h3>
          <div className="hits-list">
            {result.hits.map((hit) => (
              <div
                key={hit.rule_id}
                className="hit-card"
                style={{
                  borderLeftColor: hit.severity === "high" ? "#ef4444" : 
                                   hit.severity === "medium" ? "#f59e0b" : "#22c55e",
                }}
              >
                <div className="hit-header">
                  <div>
                    <div className="hit-title">{hit.title}</div>
                    <div className="hit-meta">
                      {hit.rule_id} • weight: {hit.weight}
                    </div>
                  </div>
                  <SeverityBadge severity={hit.severity} size="sm" />
                </div>
                <p className="hit-explain">{hit.explain}</p>
                {hit.tags.length > 0 && (
                  <div className="chips">
                    {hit.tags.map((tag) => (
                      <span key={tag} className="chip">{tag}</span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* No hits message */}
      {result.hits.length === 0 && (
        <div className="success-box">
          ✅ No phishing indicators detected. This email appears safe.
        </div>
      )}
    </div>
  );
}
