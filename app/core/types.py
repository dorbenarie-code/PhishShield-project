from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Action(str, Enum):
    allow = "allow"
    verify_out_of_band = "verify_out_of_band"
    report = "report"
    block = "block"


class PatternType(str, Enum):
    keyword = "keyword"
    regex = "regex"


class RulePattern(BaseModel):
    """
    A single atomic matcher used by the rule engine.

    - keyword: plain substring (case-insensitive matching done in engine)
    - regex: Python regex with optional flags
    """
    model_config = ConfigDict(extra="forbid", frozen=True)

    type: PatternType
    value: str = Field(min_length=1)
    flags: str | None = Field(
        default=None,
        description="Regex flags as a compact string: i,m,s (ignorecase, multiline, dotall).",
    )
    label: str | None = Field(
        default=None,
        description="Optional label shown in evidence (useful for UI).",
    )


class RuleWhen(BaseModel):
    """
    Matching configuration:
    - match=any: at least one pattern must match
    - match=all: every configured pattern must match at least once

    You can define matchers via:
    - any_keywords: list[str]
    - regex: list[str] (or a single string)
    - patterns: list[RulePattern]
    """
    model_config = ConfigDict(extra="forbid", frozen=True)

    match: Literal["any", "all"] = "any"
    any_keywords: list[str] = Field(default_factory=list)
    regex: list[str] = Field(default_factory=list)
    patterns: list[RulePattern] = Field(default_factory=list)

    @field_validator("any_keywords", mode="before")
    @classmethod
    def _coerce_keywords(cls, v: Any) -> list[str]:
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        return list(v)

    @field_validator("regex", mode="before")
    @classmethod
    def _coerce_regex(cls, v: Any) -> list[str]:
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        return list(v)


class Rule(BaseModel):
    """
    A YAML-loaded rule.
    """
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=3, max_length=64)
    title: str = Field(min_length=3, max_length=200)
    weight: int = Field(ge=0, le=100)
    severity: Severity
    when: RuleWhen
    explain: str = Field(min_length=3, max_length=2000)
    action: Action
    tags: list[str] = Field(default_factory=list)
    enabled: bool = True

    @field_validator("id")
    @classmethod
    def _normalize_id(cls, v: str) -> str:
        return v.strip()

    @field_validator("tags", mode="before")
    @classmethod
    def _coerce_tags(cls, v: Any) -> list[str]:
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        return list(v)


class Evidence(BaseModel):
    """
    Concrete proof of why a rule hit.
    start/end are character offsets in the analyzed text.
    """
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["keyword", "regex"]
    pattern: str
    match: str
    start: int = Field(ge=0)
    end: int = Field(ge=0)
    snippet: str
    label: str | None = None

    @model_validator(mode="after")
    def _validate_span(self) -> "Evidence":
        if self.end < self.start:
            raise ValueError("Evidence.end must be >= Evidence.start")
        return self


class RuleHit(BaseModel):
    """
    A single rule that matched + its evidence.
    """
    model_config = ConfigDict(extra="forbid", frozen=True)

    rule_id: str
    title: str
    weight: int
    severity: Severity
    action: Action
    explain: str
    tags: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)

    @model_validator(mode="after")
    def _ensure_evidence(self) -> "RuleHit":
        if not self.evidence:
            raise ValueError("RuleHit must include at least 1 evidence item")
        return self


class TextHighlight(BaseModel):
    """
    UI-friendly highlight span (derived from Evidence).
    """
    model_config = ConfigDict(extra="forbid", frozen=True)

    start: int = Field(ge=0)
    end: int = Field(ge=0)
    rule_id: str
    label: str

    @model_validator(mode="after")
    def _validate_span(self) -> "TextHighlight":
        if self.end < self.start:
            raise ValueError("TextHighlight.end must be >= TextHighlight.start")
        return self


class AnalysisResult(BaseModel):
    """
    Final explainable output.
    """
    model_config = ConfigDict(extra="forbid", frozen=True)

    score: int = Field(ge=0, le=100)
    severity: Severity
    action: Action
    recommendations: list[str] = Field(default_factory=list)
    hits: list[RuleHit] = Field(default_factory=list)
    highlights: list[TextHighlight] = Field(default_factory=list)
