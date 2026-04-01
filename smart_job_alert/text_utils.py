from __future__ import annotations

import re


_WS_RE = re.compile(r"\s+")


def normalize_text(s: str) -> str:
    s = (s or "").strip()
    s = _WS_RE.sub(" ", s)
    return s


def contains_any(haystack: str, needles: list[str]) -> bool:
    h = (haystack or "").lower()
    return any((n or "").lower() in h for n in needles if (n or "").strip())


def keyword_count(haystack: str, needles: list[str]) -> int:
    h = (haystack or "").lower()
    return sum(1 for n in needles if (n or "").strip() and (n or "").lower() in h)

