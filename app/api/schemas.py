from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.types import Action, RuleHit, Severity, TextHighlight


class AttachmentMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    filename: str = Field(min_length=1, max_length=260)
    size_bytes: int | None = Field(default=None, ge=0)


class AnalyzeRequest(BaseModel):
    """
    API input contract.
    Keep it flexible: subject/body/headers/attachments are optional but at least one must exist.
    """
    model_config = ConfigDict(extra="forbid")

    subject: str = Field(default="", max_length=5000)
    body: str = Field(default="", max_length=200000)
    from_email: str | None = Field(default=None, max_length=320)
    reply_to: str | None = Field(default=None, max_length=320)
    headers_raw: str | None = Field(default=None, max_length=200000)
    attachments: list[AttachmentMeta] = Field(default_factory=list, max_length=50)

    @field_validator("subject", "body", mode="before")
    @classmethod
    def _coerce_text(cls, v):
        if v is None:
            return ""
        return str(v)

    @field_validator("from_email", "reply_to", mode="before")
    @classmethod
    def _coerce_emailish(cls, v):
        if v is None:
            return None
        s = str(v).strip()
        return s or None

    @model_validator(mode="after")
    def _require_some_content(self):
        has_text = bool(self.subject.strip() or self.body.strip() or (self.headers_raw or "").strip())
        has_attachments = bool(self.attachments)
        if not (has_text or has_attachments):
            raise ValueError("Request must include at least subject/body/headers_raw or attachments.")
        return self


class AnalyzeResponse(BaseModel):
    """
    API output contract (flattened).
    """
    model_config = ConfigDict(extra="forbid")

    score: int = Field(ge=0, le=100)
    severity: Severity
    action: Action
    recommendations: list[str] = Field(default_factory=list)
    hits: list[RuleHit] = Field(default_factory=list)
    highlights: list[TextHighlight] = Field(default_factory=list)


class RuleSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    weight: int
    severity: Severity
    tags: list[str] = Field(default_factory=list)
