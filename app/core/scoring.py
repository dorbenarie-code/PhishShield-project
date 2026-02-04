from __future__ import annotations

import math
from typing import Sequence

from app.core.types import Action, AnalysisResult, RuleHit, Severity, TextHighlight


def normalize_score(raw_points: int) -> int:
    """
    Convert raw weights sum to 0-100 with diminishing returns.
    """
    raw_points = max(0, int(raw_points))
    score = int(round(100 * (1 - math.exp(-raw_points / 35))))
    return max(0, min(100, score))


def severity_from_score(score: int) -> Severity:
    if score >= 70:
        return Severity.high
    if score >= 30:
        return Severity.medium
    return Severity.low


_ACTION_PRIORITY: dict[Action, int] = {
    Action.allow: 0,
    Action.report: 1,
    Action.verify_out_of_band: 2,
    Action.block: 3,
}


def choose_action(score_severity: Severity, hits: Sequence[RuleHit]) -> Action:
    """
    Base action by severity + escalation by the strongest hit action.
    """
    base = {
        Severity.low: Action.allow,
        Severity.medium: Action.verify_out_of_band,
        Severity.high: Action.block,
    }[score_severity]

    top = base
    for h in hits:
        if _ACTION_PRIORITY[h.action] > _ACTION_PRIORITY[top]:
            top = h.action

    # Ensure severity baseline is enforced
    return top if _ACTION_PRIORITY[top] >= _ACTION_PRIORITY[base] else base


def recommendations(action: Action, severity: Severity) -> list[str]:
    """
    Return recommendations based on the chosen action (not just severity).
    This ensures consistency: action=block → recommend block actions.
    """
    if action == Action.block:
        return ["block", "report"]
    if action == Action.verify_out_of_band:
        return ["verify_out_of_band", "report_if_confirmed"]
    if action == Action.report:
        return ["report", "educate_user"]
    return ["allow", "educate_user"]


def build_highlights(hits: Sequence[RuleHit]) -> list[TextHighlight]:
    seen: set[tuple[int, int, str]] = set()
    out: list[TextHighlight] = []
    for h in hits:
        for ev in h.evidence:
            key = (ev.start, ev.end, h.rule_id)
            if key in seen:
                continue
            seen.add(key)
            out.append(
                TextHighlight(
                    start=ev.start,
                    end=ev.end,
                    rule_id=h.rule_id,
                    label=h.title,
                )
            )
    out.sort(key=lambda x: (x.start, x.end))
    return out


_SEVERITY_ORDER: dict[Severity, int] = {
    Severity.low: 0,
    Severity.medium: 1,
    Severity.high: 2,
}


def _max_severity(hits: Sequence[RuleHit]) -> Severity:
    """Return the highest severity among all hits."""
    top = Severity.low
    for h in hits:
        if _SEVERITY_ORDER[h.severity] > _SEVERITY_ORDER[top]:
            top = h.severity
    return top


def score_to_result(hits: Sequence[RuleHit]) -> AnalysisResult:
    # Count each rule once (avoid overweighting repeated matches of same rule)
    unique = {}
    for h in hits:
        unique[h.rule_id] = h

    unique_hits = list(unique.values())

    raw_points = sum(h.weight for h in unique_hits)
    score = normalize_score(raw_points)

    # 1) Base severity by score
    sev_by_score = severity_from_score(score)

    # 2) Escalate by strongest hit severity (a single high-severity hit should not be low overall)
    sev_by_hits = _max_severity(unique_hits)

    sev = sev_by_hits if _SEVERITY_ORDER[sev_by_hits] > _SEVERITY_ORDER[sev_by_score] else sev_by_score

    act = choose_action(sev, unique_hits)

    return AnalysisResult(
        score=score,
        severity=sev,
        action=act,
        recommendations=recommendations(act, sev),
        hits=unique_hits,
        highlights=build_highlights(unique_hits),
    )
