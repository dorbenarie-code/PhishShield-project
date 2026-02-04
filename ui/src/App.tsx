/**
 * PhishShield - Main Application
 * SOC-grade phishing email analyzer with explainable risk scoring
 */

import { useRef, useState } from "react";
import type { AnalyzeRequest, AnalyzeResponse } from "./api/types";
import { analyzeEmail } from "./api/client";
import { buildAnalyzedText } from "./lib/buildAnalyzedText";
import { AnalyzerForm } from "./components/AnalyzerForm";
import { ResultsPanel } from "./components/ResultsPanel";
import { HighlightedText } from "./components/HighlightedText";
import { RulePackPanel } from "./components/RulePackPanel";

export default function App() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lastPayload, setLastPayload] = useState<AnalyzeRequest | null>(null);
  const [showRules, setShowRules] = useState(false);

  const abortRef = useRef<AbortController | null>(null);

  async function onAnalyze(payload: AnalyzeRequest) {
    setError(null);
    setResult(null);
    setLastPayload(payload);

    // Cancel any pending request
    abortRef.current?.abort();
    abortRef.current = new AbortController();

    setLoading(true);
    try {
      const res = await analyzeEmail(payload);
      setResult(res);
    } catch (e: unknown) {
      // Don't show error for aborted requests
      if (e instanceof Error && e.name === "AbortError") return;
      setError(e instanceof Error ? e.message : "Unexpected error during analysis.");
    } finally {
      setLoading(false);
    }
  }

  const analyzedText = lastPayload ? buildAnalyzedText(lastPayload) : "";

  return (
    <div className="app">
      {/* Header */}
      <header className="topbar">
        <div className="topbar-left">
          <h1 className="brand">🛡️ PhishShield</h1>
          <span className="tagline">Explainable Phishing Risk Scoring</span>
        </div>
        <div className="topbar-right">
          <button 
            className={`btn btn-ghost ${showRules ? "active" : ""}`}
            onClick={() => setShowRules(!showRules)}
          >
            📋 {showRules ? "Hide" : "Show"} Rules
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="main-layout">
        {/* Left Column: Form */}
        <section className="column column-form">
          <AnalyzerForm onAnalyze={onAnalyze} loading={loading} />
        </section>

        {/* Right Column: Results */}
        <section className="column column-results">
          {/* Rule Pack Panel (toggleable) */}
          {showRules && (
            <div style={{ marginBottom: 24 }}>
              <RulePackPanel />
            </div>
          )}

          {/* Results */}
          <ResultsPanel result={result} error={error} analyzedText={analyzedText} />

          {/* Highlighted Text */}
          {result && analyzedText && (
            <div style={{ marginTop: 24 }}>
              <HighlightedText text={analyzedText} highlights={result.highlights ?? []} />
            </div>
          )}
        </section>
      </main>

      {/* Footer */}
      <footer className="footer">
        <span>PhishShield v0.1.0</span>
        <span className="footer-sep">•</span>
        <span>Backend: localhost:8000</span>
        <span className="footer-sep">•</span>
        <span>Built with FastAPI + React</span>
      </footer>
    </div>
  );
}
