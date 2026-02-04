# app/core/extractors.py
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable
from urllib.parse import urlsplit

# Characters that often wrap URLs in emails/chats.
_WRAPPING_CHARS = "\"'<>[](){}"

# Characters that commonly trail URLs (punctuation) in sentences.
_TRAILING_PUNCT = ".,;:!?…"

# A pragmatic URL regex:
# - captures http/https URLs
# - stops at whitespace
# - keeps most valid URL characters
_URL_RE = re.compile(r"(?i)\bhttps?://[^\s<>\]]+")

# Simple, safe email regex (good enough for phishing detection signals)
_EMAIL_RE = re.compile(
    r"(?i)\b[a-z0-9._%+-]{1,64}@(?:[a-z0-9-]{1,63}\.)+[a-z]{2,63}\b"
)

# Very pragmatic phone regex (international-ish). We keep it conservative to avoid FP.
_PHONE_RE = re.compile(
    r"""
    (?<!\w)
    (?:\+?\d{1,3}[\s-]?)?          # optional country code
    (?:\(?\d{2,4}\)?[\s-]?)        # area / operator
    \d{3}[\s-]?\d{4}               # local
    (?!\w)
    """,
    re.VERBOSE,
)

# Common URL shorteners (extendable)
_SHORTENER_DOMAINS = {
    "bit.ly",
    "t.co",
    "tinyurl.com",
    "goo.gl",
    "ow.ly",
    "is.gd",
    "buff.ly",
    "cutt.ly",
    "rebrand.ly",
    "shorturl.at",
}


@dataclass(frozen=True)
class ExtractedArtifacts:
    """
    Structured artifacts extracted from message text.
    Keep it small and stable; it's meant for rules/services, not UI.
    """

    urls: list[str]
    domains: list[str]
    emails: list[str]
    phones: list[str]


def extract_all(text: str) -> ExtractedArtifacts:
    """
    Convenience helper: extract urls/domains/emails/phones from text.
    """
    urls = extract_urls(text)
    domains = extract_domains(urls)
    emails = extract_emails(text)
    phones = extract_phones(text)
    return ExtractedArtifacts(urls=urls, domains=domains, emails=emails, phones=phones)


def extract_urls(text: str) -> list[str]:
    """
    Extract http/https URLs from text, with cleanup:
    - removes wrapping quotes/brackets
    - trims trailing punctuation
    - balances common wrapping pairs (e.g. "(https://x.com)")
    Returns unique URLs in appearance order.
    """
    if not text:
        return []

    out: list[str] = []
    seen: set[str] = set()

    for m in _URL_RE.finditer(text):
        raw = m.group(0)
        url = _clean_url(raw)
        if not url:
            continue
        if url in seen:
            continue
        seen.add(url)
        out.append(url)

    return out


def _clean_url(url: str) -> str:
    """
    Clean a URL candidate without being too clever.
    The goal is stable extraction, not full RFC compliance.
    """
    if not url:
        return ""

    s = url.strip()

    # Strip wrapping characters from both ends (quotes/brackets/etc.)
    s = s.strip(_WRAPPING_CHARS)

    # Trim trailing punctuation repeatedly (".", ",", "!", "…", etc.)
    while s and s[-1] in _TRAILING_PUNCT:
        s = s[:-1]

    # Strip trailing wrapping characters that may have been exposed after punctuation removal
    # e.g., "https://example.com/path?a=1)," -> after comma removal -> "https://example.com/path?a=1)"
    while s and s[-1] in _WRAPPING_CHARS:
        s = s[:-1]

    # Balance one-layer parentheses/brackets if user wrote "(https://...)" etc.
    s = _strip_balanced_wrappers(s)

    # Quick sanity check: must still look like a URL
    if not s.lower().startswith(("http://", "https://")):
        return ""

    # Ensure we can parse a host
    try:
        parts = urlsplit(s)
    except Exception:
        return ""

    if not parts.netloc:
        return ""

    # Remove trailing dot in host (rare, but exists in some texts)
    # We do not rewrite the full URL; just return cleaned string.
    return s


def _strip_balanced_wrappers(s: str) -> str:
    """
    Remove one level of balanced wrappers if present.
    Example: "(https://x)" -> "https://x"
    """
    if len(s) < 2:
        return s

    pairs = {("(", ")"), ("[", "]"), ("{", "}"), ("<", ">"), ('"', '"'), ("'", "'")}
    for left, right in pairs:
        if s.startswith(left) and s.endswith(right):
            return s[1:-1].strip()
    return s


def extract_domains(urls: Iterable[str]) -> list[str]:
    """
    Extract normalized domains from URLs:
    - lowercased
    - strips port
    - strips leading 'www.'
    Returns unique domains in appearance order.
    """
    out: list[str] = []
    seen: set[str] = set()

    for u in urls:
        d = domain_from_url(u)
        if not d:
            continue
        if d in seen:
            continue
        seen.add(d)
        out.append(d)

    return out


def domain_from_url(url: str) -> str:
    """
    Parse and normalize the hostname from a URL.
    """
    if not url:
        return ""

    try:
        parts = urlsplit(url)
    except Exception:
        return ""

    host = (parts.hostname or "").strip().lower()
    if not host:
        return ""

    if host.startswith("www."):
        host = host[4:]

    # Basic cleanup (avoid ending dot)
    host = host.rstrip(".")

    return host


def extract_emails(text: str) -> list[str]:
    """
    Extract email addresses from text.
    Returns unique emails in appearance order (lowercased).
    """
    if not text:
        return []

    out: list[str] = []
    seen: set[str] = set()

    for m in _EMAIL_RE.finditer(text):
        email = m.group(0).lower()
        if email in seen:
            continue
        seen.add(email)
        out.append(email)

    return out


def extract_phones(text: str) -> list[str]:
    """
    Extract phone-like numbers (conservative).
    Returns unique phones in appearance order as normalized digits with optional leading '+'.

    Note: This is optional signal only. Expect some FP; keep weights low if you add phone rules.
    """
    if not text:
        return []

    out: list[str] = []
    seen: set[str] = set()

    for m in _PHONE_RE.finditer(text):
        raw = m.group(0).strip()
        norm = _normalize_phone(raw)
        if not norm:
            continue
        if norm in seen:
            continue
        seen.add(norm)
        out.append(norm)

    return out


def _normalize_phone(s: str) -> str:
    """
    Normalize a phone string:
    - keep leading '+'
    - keep digits only otherwise
    - require a minimum digit length to reduce false positives
    """
    if not s:
        return ""

    s = s.strip()
    plus = s.startswith("+")
    digits = re.sub(r"\D+", "", s)

    # Too short => likely not a phone
    if len(digits) < 9:
        return ""

    return ("+" if plus else "") + digits


# --- helper checks for rules/services (optional but handy) ---

def is_shortener_domain(domain: str) -> bool:
    d = (domain or "").strip().lower()
    if d.startswith("www."):
        d = d[4:]
    return d in _SHORTENER_DOMAINS


def is_punycode_domain(domain: str) -> bool:
    d = (domain or "").lower()
    return "xn--" in d


def subdomain_count(domain: str) -> int:
    """
    Count labels in domain. Example:
      a.b.c.example.com -> 6 labels
    """
    d = (domain or "").strip(".").lower()
    if not d:
        return 0
    return len([p for p in d.split(".") if p])
