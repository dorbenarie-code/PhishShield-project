from __future__ import annotations

# We intentionally keep normalization "index-safe":
# do not remove chars (it breaks spans), only replace with same-length placeholders.
_ZERO_WIDTH = {
    "\u200b",  # zero width space
    "\u200c",  # zero width non-joiner
    "\u200d",  # zero width joiner
    "\ufeff",  # BOM / zero width no-break space
}


def normalize_for_matching(text: str) -> str:
    """
    Lowercases and replaces zero-width characters with spaces.
    Keeps length stable so offsets (spans) still match the original text.
    """
    if not text:
        return ""
    out = []
    for ch in text:
        out.append(" " if ch in _ZERO_WIDTH else ch)
    return "".join(out).lower()
