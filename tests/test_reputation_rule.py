"""
Tests for CTX-URL-REPUTATION rule.

Uses monkeypatching to avoid real API calls.
"""
from app.core.analyzer import Analyzer
from app.services.url_reputation import ReputationResult


def test_reputation_rule_monkeypatched(monkeypatch):
    """Test that malicious domains trigger CTX-URL-REPUTATION rule."""
    a = Analyzer()

    # Patch the engine's internal reputation service
    rep = a.engine._reputation  # type: ignore[attr-defined]
    rep.enabled = True

    def fake_lookup(domain: str):
        if domain == "bad.example":
            return ReputationResult(domain=domain, malicious=2, suspicious=0, harmless=0, undetected=0)
        return None

    monkeypatch.setattr(rep, "lookup_domain", fake_lookup)

    res = a.analyze(
        subject="Hi",
        body="Go to https://bad.example/login",
        from_email="support@example.com",
    )

    ids = {h.rule_id for h in res.hits}
    assert "CTX-URL-REPUTATION" in ids
    assert res.score >= 1


def test_reputation_rule_suspicious_domain(monkeypatch):
    """Test that suspicious (not malicious) domains also trigger the rule with lower weight."""
    a = Analyzer()

    rep = a.engine._reputation  # type: ignore[attr-defined]
    rep.enabled = True

    def fake_lookup(domain: str):
        if domain == "suspicious.example":
            return ReputationResult(domain=domain, malicious=0, suspicious=3, harmless=10, undetected=5)
        return None

    monkeypatch.setattr(rep, "lookup_domain", fake_lookup)

    res = a.analyze(
        subject="Check this",
        body="Visit https://suspicious.example/page",
        from_email="info@company.com",
    )

    ids = {h.rule_id for h in res.hits}
    assert "CTX-URL-REPUTATION" in ids

    # Find the reputation hit and verify weight is 18 (suspicious, not malicious)
    rep_hit = next(h for h in res.hits if h.rule_id == "CTX-URL-REPUTATION")
    assert rep_hit.weight == 18


def test_reputation_rule_disabled_no_hit(monkeypatch):
    """When reputation service is disabled, no CTX-URL-REPUTATION hit should occur."""
    a = Analyzer()

    rep = a.engine._reputation  # type: ignore[attr-defined]
    rep.enabled = False  # Disabled

    res = a.analyze(
        subject="Hi",
        body="Go to https://bad.example/login",
        from_email="support@example.com",
    )

    ids = {h.rule_id for h in res.hits}
    assert "CTX-URL-REPUTATION" not in ids


def test_reputation_rule_clean_domain_no_hit(monkeypatch):
    """Clean domains should not trigger CTX-URL-REPUTATION."""
    a = Analyzer()

    rep = a.engine._reputation  # type: ignore[attr-defined]
    rep.enabled = True

    def fake_lookup(domain: str):
        # All domains are clean
        return ReputationResult(domain=domain, malicious=0, suspicious=0, harmless=50, undetected=10)

    monkeypatch.setattr(rep, "lookup_domain", fake_lookup)

    res = a.analyze(
        subject="Newsletter",
        body="Read more at https://clean.example/article",
        from_email="news@company.com",
    )

    ids = {h.rule_id for h in res.hits}
    assert "CTX-URL-REPUTATION" not in ids

