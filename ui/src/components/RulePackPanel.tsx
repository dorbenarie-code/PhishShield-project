/**
 * RulePackPanel - Displays loaded rules with search capability
 * Useful for SOC analysts and demo purposes to show rule coverage
 */

import { useEffect, useMemo, useState } from "react";
import type { RuleSummary } from "../api/types";
import { fetchRules } from "../api/client";
import { SeverityBadge } from "./SeverityBadge";

export function RulePackPanel() {
  const [rules, setRules] = useState<RuleSummary[]>([]);
  const [query, setQuery] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRules()
      .then((data) => {
        setRules(data);
        setLoading(false);
      })
      .catch((e) => {
        setError(e instanceof Error ? e.message : "Failed to load rules");
        setLoading(false);
      });
  }, []);

  // Filter rules by search query (id, title, tags)
  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return rules;
    return rules.filter((r) =>
      `${r.id} ${r.title} ${(r.tags ?? []).join(" ")}`.toLowerCase().includes(q)
    );
  }, [query, rules]);

  // Group rules by severity for stats
  const stats = useMemo(() => {
    const counts = { high: 0, medium: 0, low: 0 };
    for (const r of rules) {
      counts[r.severity]++;
    }
    return counts;
  }, [rules]);

  if (loading) {
    return (
      <div className="panel">
        <div className="panel-header">
          <h3 className="panel-title small">📋 Rule Pack</h3>
        </div>
        <div className="panel-body" style={{ padding: 20, textAlign: "center", color: "#666" }}>
          Loading rules...
        </div>
      </div>
    );
  }

  return (
    <div className="panel">
      <div className="panel-header">
        <h3 className="panel-title small">📋 Rule Pack Loaded</h3>
        <div className="subtle">{rules.length} rules</div>
      </div>

      {/* Stats bar */}
      <div className="stats-bar">
        <span className="stat">
          <span className="stat-dot high"></span>
          {stats.high} high
        </span>
        <span className="stat">
          <span className="stat-dot medium"></span>
          {stats.medium} medium
        </span>
        <span className="stat">
          <span className="stat-dot low"></span>
          {stats.low} low
        </span>
      </div>

      {/* Search input */}
      <div className="search-wrapper">
        <input
          type="text"
          className="search-input"
          placeholder="🔍 Search rule id, title, or tag..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        {query && (
          <button className="search-clear" onClick={() => setQuery("")} title="Clear search">
            ×
          </button>
        )}
      </div>

      {error && <div className="error-box">{error}</div>}

      {/* Rules list */}
      <div className="rule-list">
        {filtered.length === 0 && (
          <div className="empty-state">No rules match "{query}"</div>
        )}
        {filtered.slice(0, 50).map((r) => (
          <div key={r.id} className="rule-row">
            <div className="rule-main">
              <div className="rule-id">{r.id}</div>
              <div className="rule-title">{r.title}</div>
              {!!r.tags?.length && (
                <div className="chips">
                  {r.tags.slice(0, 5).map((t) => (
                    <span key={t} className="chip">{t}</span>
                  ))}
                </div>
              )}
            </div>
            <div className="rule-meta">
              <span className="weight-badge">w:{r.weight}</span>
              <SeverityBadge severity={r.severity} size="sm" />
            </div>
          </div>
        ))}
        {filtered.length > 50 && (
          <div className="hint subtle" style={{ padding: 12 }}>
            Showing first 50 of {filtered.length} results. Refine your search.
          </div>
        )}
      </div>
    </div>
  );
}

