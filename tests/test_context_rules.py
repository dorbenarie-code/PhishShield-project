"""
Tests for context-aware rules (CTX-* rules).

These rules use pre-extracted artifacts (URLs, domains) to detect
phishing signals that are hard to express in pure regex.
"""
from app.core.analyzer import Analyzer


def test_ctx_url_shortener_hit():
    """URL shortener domains (bit.ly, t.co, etc.) should trigger CTX-URL-SHORTENER."""
    a = Analyzer()
    res = a.analyze(
        subject="Hi",
        body="Please verify here: https://bit.ly/abc123",
        from_email="it-support@example.com",
    )
    ids = {h.rule_id for h in res.hits}
    assert "CTX-URL-SHORTENER" in ids


def test_ctx_url_punycode_hit():
    """Punycode/IDN domains (xn--) should trigger CTX-URL-PUNYCODE."""
    a = Analyzer()
    res = a.analyze(
        subject="Security Update",
        body="Open: https://xn--pple-43d.com/login",
        from_email="support@example.com",
    )
    ids = {h.rule_id for h in res.hits}
    assert "CTX-URL-PUNYCODE" in ids


def test_ctx_url_many_subdomains_hit():
    """Deep subdomain chains (5+ levels) should trigger CTX-URL-SUBDOMAINS."""
    a = Analyzer()
    res = a.analyze(
        subject="Account",
        body="Login: https://a.b.c.d.e.example.com/auth",
        from_email="support@example.com",
    )
    ids = {h.rule_id for h in res.hits}
    assert "CTX-URL-SUBDOMAINS" in ids


def test_normal_url_no_ctx_hit():
    """Normal URLs should not trigger context rules."""
    a = Analyzer()
    res = a.analyze(
        subject="Meeting",
        body="See details at https://www.google.com/calendar",
        from_email="colleague@company.com",
    )
    ctx_ids = {h.rule_id for h in res.hits if h.rule_id.startswith("CTX-")}
    assert len(ctx_ids) == 0

