from __future__ import annotations

import os
from functools import lru_cache

from fastapi import APIRouter

from app.api.schemas import AnalyzeRequest, AnalyzeResponse, RuleSummary
from app.core.analyzer import Analyzer

router = APIRouter()


@lru_cache
def get_analyzer() -> Analyzer:
    pack_path = os.getenv("PHISHSHIELD_RULE_PACK")
    return Analyzer(rule_pack_path=pack_path)


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/rules", response_model=list[RuleSummary])
def list_rules() -> list[RuleSummary]:
    engine_rules = get_analyzer().engine.rules
    return [
        RuleSummary(
            id=r.id,
            title=r.title,
            weight=r.weight,
            severity=r.severity,
            tags=r.tags,
        )
        for r in engine_rules
    ]


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(payload: AnalyzeRequest) -> AnalyzeResponse:
    analyzer = get_analyzer()
    result = analyzer.analyze(
        subject=payload.subject,
        body=payload.body,
        from_email=payload.from_email,
        reply_to=payload.reply_to,
        headers_raw=payload.headers_raw,
        attachments=[a.filename for a in payload.attachments],
    )
    return AnalyzeResponse.model_validate(result.model_dump())
