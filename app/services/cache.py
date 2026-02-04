# app/services/cache.py
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any


@dataclass
class _Entry:
    value: Any
    expires_at: float


class TTLCache:
    """
    Tiny in-memory TTL cache.
    Good enough for local demo + avoids burning API quota.
    """

    def __init__(self, ttl_seconds: int = 3600, max_items: int = 2000) -> None:
        self.ttl = max(1, int(ttl_seconds))
        self.max_items = max(50, int(max_items))
        self._data: dict[str, _Entry] = {}

    def get(self, key: str) -> Any | None:
        now = time.time()
        ent = self._data.get(key)
        if not ent:
            return None
        if ent.expires_at <= now:
            self._data.pop(key, None)
            return None
        return ent.value

    def set(self, key: str, value: Any) -> None:
        now = time.time()
        if len(self._data) >= self.max_items:
            # drop oldest-ish (cheap cleanup)
            self._purge(now, target_size=self.max_items // 2)
        self._data[key] = _Entry(value=value, expires_at=now + self.ttl)

    def _purge(self, now: float, target_size: int) -> None:
        # remove expired first
        expired = [k for k, v in self._data.items() if v.expires_at <= now]
        for k in expired:
            self._data.pop(k, None)

        if len(self._data) <= target_size:
            return

        # remove arbitrary keys (simple)
        for k in list(self._data.keys())[: max(0, len(self._data) - target_size)]:
            self._data.pop(k, None)
