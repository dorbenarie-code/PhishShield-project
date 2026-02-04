# app/core/context.py
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AnalysisContext:
    """
    Structured context passed to the rule engine for context-aware rules.
    Contains pre-extracted artifacts from the message.
    """
    urls: list[str]
    domains: list[str]
    emails: list[str]
    phones: list[str]

