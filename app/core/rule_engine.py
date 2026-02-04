# app/core/rule_engine.py
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Iterable, Sequence

from app.core.extractors import is_punycode_domain, is_shortener_domain, subdomain_count
from app.core.types import Action, Evidence, Rule, RuleHit, RulePattern, Severity
from app.services.url_reputation import UrlReputationService
from app.utils.text_norm import normalize_for_matching

if TYPE_CHECKING:
    from app.core.context import AnalysisContext

logger = logging.getLogger(__name__)


class RulePackError(RuntimeError):
    """Raised when a rule pack is missing/invalid."""


_FLAG_MAP: dict[str, int] = {
    "i": re.IGNORECASE,
    "m": re.MULTILINE,
    "s": re.DOTALL,
}


def _compile_flags(flags: str | None) -> int:
    """
    Build regex flags from string.

    - flags=None  → default IGNORECASE | MULTILINE (for convenience)
    - flags provided → ONLY use the explicitly specified flags (no implicit IGNORECASE)

    Examples:
        - flags=None  → IGNORECASE | MULTILINE
        - flags="m"   → MULTILINE only (case-sensitive!)
        - flags="im"  → IGNORECASE | MULTILINE
        - flags="ims" → IGNORECASE | MULTILINE | DOTALL
    """
    if flags is None:
        return re.IGNORECASE | re.MULTILINE  # default for convenience

    # Explicit flags: only use what's specified
    value = 0
    for ch in flags:
        value |= _FLAG_MAP.get(ch.lower(), 0)
    return value


def _snippet(text: str, start: int, end: int, window: int = 48) -> str:
    left = max(0, start - window)
    right = min(len(text), end + window)
    prefix = "…" if left > 0 else ""
    suffix = "…" if right < len(text) else ""
    return f"{prefix}{text[left:right]}{suffix}"


@dataclass(frozen=True)
class _CompiledPattern:
    raw: RulePattern
    kind: str  # "keyword" | "regex"
    keyword: str | None = None
    regex: re.Pattern[str] | None = None


@dataclass(frozen=True)
class _CompiledRule:
    rule: Rule
    match_mode: str  # "any" | "all"
    patterns: tuple[_CompiledPattern, ...]


class RuleEngine:
    """
    Pure-python engine: load YAML -> validate -> execute matchers -> return hits with evidence.
    No FastAPI dependency. Safe to run in tests/CLI/workers.
    """

    def __init__(self, rules: Sequence[Rule], *, max_evidence_per_rule: int = 20) -> None:
        self._rules = [r for r in rules if r.enabled]
        self._max_evidence_per_rule = max(1, int(max_evidence_per_rule))
        self._compiled = tuple(self._compile_rule(r) for r in self._rules)
        self._reputation = UrlReputationService()

    @property
    def rules(self) -> Sequence[Rule]:
        return self._rules

    @classmethod
    def from_yaml(cls, path: str | Path, *, max_evidence_per_rule: int = 20) -> "RuleEngine":
        path = Path(path)
        if not path.exists():
            raise RulePackError(f"Rule pack not found: {path}")

        try:
            import yaml  # type: ignore
        except Exception as e:  # pragma: no cover
            raise RulePackError("Missing dependency: PyYAML (pip install pyyaml)") from e

        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception as e:
            raise RulePackError(f"Failed to parse YAML: {path}") from e

        if not isinstance(raw, list):
            raise RulePackError(f"Rule pack must be a YAML list (top-level array). Got: {type(raw)}")

        rules: list[Rule] = []
        for idx, item in enumerate(raw):
            if not isinstance(item, dict):
                raise RulePackError(f"Rule at index {idx} must be a mapping/dict. Got: {type(item)}")
            try:
                rules.append(Rule.model_validate(item))
            except Exception as e:
                raise RulePackError(f"Invalid rule schema at index {idx} (id={item.get('id')}): {e}") from e

        engine = cls(rules, max_evidence_per_rule=max_evidence_per_rule)

        # Validate regex compilation early (fail-fast).
        for cr in engine._compiled:
            for cp in cr.patterns:
                if cp.kind == "regex" and cp.regex is None:
                    raise RulePackError(f"Regex compilation failed for rule {cr.rule.id}: {cp.raw.value}")

        return engine

    def match(self, text: str, ctx: "AnalysisContext | None" = None) -> list[RuleHit]:
        """
        Execute all YAML rules against the given text, plus (optional) context rules.
        Returns RuleHit objects with evidence+spans for every hit.
        """
        if not text:
            return []

        haystack = normalize_for_matching(text)
        hits: list[RuleHit] = []

        # 1) YAML-backed rules
        for cr in self._compiled:
            evidence: list[Evidence] = []

            if cr.match_mode == "all":
                # In "all" mode: every pattern must match at least once.
                # We only need ONE evidence per pattern to prove it matched.
                ok = True
                for cp in cr.patterns:
                    ev = list(self._match_one(cp, text, haystack))
                    if not ev:
                        ok = False
                        break
                    # Take only the first evidence for this pattern (proof it matched)
                    evidence.append(ev[0])
                    if len(evidence) >= self._max_evidence_per_rule:
                        break

                if ok and evidence:
                    hits.append(self._to_hit(cr.rule, evidence))

            else:  # any
                for cp in cr.patterns:
                    for ev in self._match_one(cp, text, haystack):
                        evidence.append(ev)
                        if len(evidence) >= self._max_evidence_per_rule:
                            break
                    if len(evidence) >= self._max_evidence_per_rule:
                        break

                if evidence:
                    hits.append(self._to_hit(cr.rule, evidence))

        # 2) Context rules (hard-coded, SOC-like)
        if ctx is not None:
            hits.extend(self._context_hits(text, haystack, ctx))

        return hits

    # -------------------- Context Rules --------------------

    def _context_hits(self, text: str, haystack: str, ctx: "AnalysisContext") -> list[RuleHit]:
        out: list[RuleHit] = []

        # CTX-URL-SHORTENER
        shortener_domains = [d for d in ctx.domains if is_shortener_domain(d)]
        if shortener_domains:
            ev = self._evidence_for_any_token(text, haystack, ctx.urls, shortener_domains, kind="keyword")
            if ev:
                out.append(
                    RuleHit(
                        rule_id="CTX-URL-SHORTENER",
                        title="URL shortener detected",
                        weight=14,
                        severity=Severity.high,
                        action=Action.block,
                        explain="Shortened URLs hide the real destination and are commonly used in phishing.",
                        tags=["links", "context"],
                        evidence=[ev],
                    )
                )

        # CTX-URL-PUNYCODE
        puny_domains = [d for d in ctx.domains if is_punycode_domain(d)]
        if puny_domains:
            ev = self._evidence_for_any_token(text, haystack, ctx.urls, puny_domains, kind="keyword")
            if ev:
                out.append(
                    RuleHit(
                        rule_id="CTX-URL-PUNYCODE",
                        title="Punycode/IDN domain detected",
                        weight=12,
                        severity=Severity.high,
                        action=Action.block,
                        explain="Punycode domains (xn--) can be used for lookalike attacks via international characters.",
                        tags=["links", "context"],
                        evidence=[ev],
                    )
                )

        # CTX-URL-SUBDOMAINS
        # count labels, e.g. a.b.c.d.e.example.com -> 7 labels
        many_subdomains = [d for d in ctx.domains if subdomain_count(d) >= 5]
        if many_subdomains:
            ev = self._evidence_for_any_token(text, haystack, ctx.urls, many_subdomains, kind="keyword")
            if ev:
                out.append(
                    RuleHit(
                        rule_id="CTX-URL-SUBDOMAINS",
                        title="Suspiciously deep subdomain chain",
                        weight=10,
                        severity=Severity.medium,
                        action=Action.verify_out_of_band,
                        explain="Very deep subdomain chains are often used to impersonate trusted domains.",
                        tags=["links", "context"],
                        evidence=[ev],
                    )
                )

        # CTX-URL-REPUTATION (VirusTotal)
        if self._reputation.enabled:
            flagged = []
            for d in ctx.domains:
                res = self._reputation.lookup_domain(d)
                if res and (res.malicious > 0 or res.suspicious > 0):
                    flagged.append(res)

            if flagged:
                # pick top domain (most malicious/suspicious)
                top = sorted(flagged, key=lambda x: (x.malicious, x.suspicious), reverse=True)[0]
                ev = self._evidence_for_any_token(text, haystack, ctx.urls, [top.domain], kind="keyword")
                if ev:
                    # weight: malicious stronger than suspicious
                    weight = 25 if top.malicious > 0 else 18
                    out.append(
                        RuleHit(
                            rule_id="CTX-URL-REPUTATION",
                            title="Domain flagged by reputation service",
                            weight=weight,
                            severity=Severity.high,
                            action=Action.block,
                            explain="External reputation service reports this domain as malicious/suspicious.",
                            tags=["links", "intel", "context"],
                            evidence=[ev],
                        )
                    )

        return out

    def _evidence_for_any_token(
        self,
        text: str,
        haystack: str,
        urls: Sequence[str],
        domains: Sequence[str],
        *,
        kind: str,
    ) -> Evidence | None:
        """
        Try to create a clean Evidence for CTX rules.
        Prefer URL match; fallback to domain match. Uses normalized haystack to locate spans reliably.
        """
        # Prefer URL span
        for u in urls:
            if not u:
                continue
            idx = haystack.find(u.lower())
            if idx != -1:
                end = idx + len(u)
                return Evidence(
                    kind=kind,
                    pattern="context:url",
                    match=text[idx:end],
                    start=idx,
                    end=end,
                    snippet=_snippet(text, idx, end),
                    label="url",
                )

        # Fallback domain span
        for d in domains:
            if not d:
                continue
            idx = haystack.find(d.lower())
            if idx != -1:
                end = idx + len(d)
                return Evidence(
                    kind=kind,
                    pattern="context:domain",
                    match=text[idx:end],
                    start=idx,
                    end=end,
                    snippet=_snippet(text, idx, end),
                    label="domain",
                )

        return None

    # -------------------- YAML Rule Compilation & Matching --------------------

    def _compile_rule(self, rule: Rule) -> _CompiledRule:
        patterns: list[RulePattern] = []

        for kw in rule.when.any_keywords:
            if kw and kw.strip():
                patterns.append(RulePattern(type="keyword", value=kw.strip(), label="keyword"))

        for rg in rule.when.regex:
            if rg and rg.strip():
                patterns.append(RulePattern(type="regex", value=rg.strip(), flags=None, label="regex"))

        patterns.extend(rule.when.patterns)

        compiled: list[_CompiledPattern] = []
        for p in patterns:
            if p.type.value == "keyword":
                compiled.append(
                    _CompiledPattern(
                        raw=p,
                        kind="keyword",
                        keyword=p.value.lower(),
                        regex=None,
                    )
                )
            elif p.type.value == "regex":
                flags = _compile_flags(p.flags)
                try:
                    rx = re.compile(p.value, flags=flags)
                except re.error as e:
                    raise RulePackError(f"Invalid regex in rule {rule.id}: {p.value}. Error: {e}") from e
                compiled.append(_CompiledPattern(raw=p, kind="regex", keyword=None, regex=rx))
            else:
                raise RulePackError(f"Unsupported pattern type in rule {rule.id}: {p.type}")

        if not compiled:
            raise RulePackError(f"Rule {rule.id} has no matchers in 'when'.")

        return _CompiledRule(rule=rule, match_mode=rule.when.match, patterns=tuple(compiled))

    def _to_hit(self, rule: Rule, evidence: Sequence[Evidence]) -> RuleHit:
        return RuleHit(
            rule_id=rule.id,
            title=rule.title,
            weight=rule.weight,
            severity=rule.severity,
            action=rule.action,
            explain=rule.explain,
            tags=rule.tags,
            evidence=list(evidence),
        )

    def _match_one(self, cp: _CompiledPattern, text: str, haystack: str) -> Iterable[Evidence]:
        if cp.kind == "keyword":
            assert cp.keyword is not None
            return self._find_keyword(text, haystack, cp.keyword, label=cp.raw.label, pattern=cp.raw.value)

        if cp.kind == "regex":
            assert cp.regex is not None
            return self._find_regex(text, cp.regex, label=cp.raw.label, pattern=cp.raw.value)

        return []

    def _find_keyword(
        self,
        text: str,
        haystack: str,
        needle: str,
        *,
        label: str | None,
        pattern: str,
        max_per_keyword: int = 8,
    ) -> Iterable[Evidence]:
        if not needle:
            return []

        out: list[Evidence] = []
        start = 0
        count = 0
        while True:
            idx = haystack.find(needle, start)
            if idx == -1:
                break
            end = idx + len(needle)
            out.append(
                Evidence(
                    kind="keyword",
                    pattern=pattern,
                    match=text[idx:end],
                    start=idx,
                    end=end,
                    snippet=_snippet(text, idx, end),
                    label=label,
                )
            )
            count += 1
            if count >= max_per_keyword:
                break
            start = end

        return out

    def _find_regex(
        self,
        text: str,
        rx: re.Pattern[str],
        *,
        label: str | None,
        pattern: str,
        max_per_regex: int = 10,
    ) -> Iterable[Evidence]:
        out: list[Evidence] = []
        for m in rx.finditer(text):
            s, e = m.span()
            if s == e:
                continue
            out.append(
                Evidence(
                    kind="regex",
                    pattern=pattern,
                    match=m.group(0),
                    start=s,
                    end=e,
                    snippet=_snippet(text, s, e),
                    label=label,
                )
            )
            if len(out) >= max_per_regex:
                break
        return out
