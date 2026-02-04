# app/core/analyzer.py
from __future__ import annotations

from pathlib import Path
from typing import Iterable

from app.core.context import AnalysisContext
from app.core.extractors import extract_all
from app.core.rule_engine import RuleEngine
from app.core.scoring import score_to_result
from app.core.types import AnalysisResult


def _default_rule_pack_path() -> Path:
    return Path(__file__).resolve().parents[1] / "rules" / "pack_default.yml"


def _join_message_parts(
    *,
    subject: str | None,
    body: str | None,
    from_email: str | None,
    reply_to: str | None,
    headers_raw: str | None,
    attachments: Iterable[str] | None,
) -> str:
    parts: list[str] = []

    if subject:
        parts.append(f"Subject: {subject}")
    if from_email:
        parts.append(f"From: {from_email}")
    if reply_to:
        parts.append(f"Reply-To: {reply_to}")
    if headers_raw:
        parts.append("Headers:")
        parts.append(headers_raw)

    if body:
        parts.append("Body:")
        parts.append(body)

    if attachments:
        parts.append("Attachments:")
        for fn in attachments:
            if fn:
                parts.append(f"- {fn}")

    return "\n".join(parts).strip()


class Analyzer:
    """
    Orchestrator: compose text -> extract artifacts -> rule engine -> scoring.
    Pure Python (no FastAPI imports).
    """

    def __init__(self, rule_pack_path: str | Path | None = None) -> None:
        path = Path(rule_pack_path) if rule_pack_path else _default_rule_pack_path()
        self.engine = RuleEngine.from_yaml(path)

    def analyze(
        self,
        *,
        subject: str | None = None,
        body: str | None = None,
        from_email: str | None = None,
        reply_to: str | None = None,
        headers_raw: str | None = None,
        attachments: list[str] | None = None,
    ) -> AnalysisResult:
        text = _join_message_parts(
            subject=subject,
            body=body,
            from_email=from_email,
            reply_to=reply_to,
            headers_raw=headers_raw,
            attachments=attachments,
        )

        art = extract_all(text)
        ctx = AnalysisContext(
            urls=art.urls,
            domains=art.domains,
            emails=art.emails,
            phones=art.phones,
        )

        hits = self.engine.match(text, ctx=ctx)
        return score_to_result(hits)
