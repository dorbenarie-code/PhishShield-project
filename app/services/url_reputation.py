# app/services/url_reputation.py
from __future__ import annotations

import os
from dataclasses import dataclass

import httpx

from app.services.cache import TTLCache


@dataclass(frozen=True)
class ReputationResult:
    domain: str
    malicious: int
    suspicious: int
    harmless: int
    undetected: int


class UrlReputationService:
    """
    VirusTotal reputation lookup (optional).
    - If no API key is configured, service is disabled.
    - Uses TTL cache to avoid quota burn.
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        timeout_seconds: float = 3.5,
        cache: TTLCache | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("VT_API_KEY") or ""
        self.enabled = bool(self.api_key.strip())
        self.timeout = float(timeout_seconds)
        self.cache = cache or TTLCache(ttl_seconds=3600, max_items=2000)

    def lookup_domain(self, domain: str) -> ReputationResult | None:
        d = (domain or "").strip().lower()
        if not d or not self.enabled:
            return None

        cache_key = f"vt:domain:{d}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        url = f"https://www.virustotal.com/api/v3/domains/{d}"
        headers = {"x-apikey": self.api_key}

        try:
            with httpx.Client(timeout=self.timeout) as client:
                r = client.get(url, headers=headers)
                if r.status_code == 404:
                    # unknown domain: treat as no intel (do not penalize)
                    self.cache.set(cache_key, None)
                    return None
                r.raise_for_status()
                data = r.json()
        except Exception:
            # If VT is down / blocked / rate-limited, fail closed (no intel) but don't break analysis
            self.cache.set(cache_key, None)
            return None

        stats = (
            data.get("data", {})
            .get("attributes", {})
            .get("last_analysis_stats", {})
        )

        res = ReputationResult(
            domain=d,
            malicious=int(stats.get("malicious", 0) or 0),
            suspicious=int(stats.get("suspicious", 0) or 0),
            harmless=int(stats.get("harmless", 0) or 0),
            undetected=int(stats.get("undetected", 0) or 0),
        )

        self.cache.set(cache_key, res)
        return res
