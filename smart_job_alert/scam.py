from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse

from .models import Job
from .text_utils import normalize_text


@dataclass(frozen=True)
class ScamResult:
    is_scam: bool
    reason: str = ""


_EMAIL_RE = re.compile(r"\b[\w.\-+]+@([\w\-]+\.[\w.\-]+)\b", re.IGNORECASE)
_URL_RE = re.compile(r"\bhttps?://[^\s)]+", re.IGNORECASE)
_MANY_CAPS_RE = re.compile(r"\b[A-Z]{5,}\b")


def _domain(url: str) -> str:
    try:
        netloc = urlparse(url).netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc
    except Exception:
        return ""


def detect_scam(
    job: Job,
    *,
    allowed_domains: list[str],
    blocked_domains: list[str],
    payment_keywords: list[str],
    min_description_chars: int,
) -> ScamResult:
    url_domain = _domain(job.url)
    allowed = {d.lower().lstrip("www.") for d in (allowed_domains or []) if (d or "").strip()}
    blocked = {d.lower().lstrip("www.") for d in (blocked_domains or []) if (d or "").strip()}

    if url_domain and url_domain in blocked:
        return ScamResult(True, f"Blocked domain: {url_domain}")

    if allowed and url_domain and url_domain not in allowed:
        return ScamResult(True, f"Domain not in allowlist: {url_domain}")

    text = " | ".join(
        [
            normalize_text(job.title),
            normalize_text(job.company),
            normalize_text(job.location),
            normalize_text(job.description),
        ]
    )
    t = text.lower()

    for kw in (payment_keywords or []):
        k = (kw or "").strip().lower()
        if k and k in t:
            return ScamResult(True, f"Payment keyword matched: {kw}")

    if job.description and len(normalize_text(job.description)) < int(min_description_chars):
        return ScamResult(True, "Description too short / low quality")

    if _MANY_CAPS_RE.search(text) and len(text) < 500:
        return ScamResult(True, "Shouty/low-quality formatting")

    emails = {m.group(1).lower().lstrip("www.") for m in _EMAIL_RE.finditer(text)}
    urls = {_domain(m.group(0)) for m in _URL_RE.finditer(text)}
    urls.discard("")

    if allowed:
        suspicious = {d for d in (emails | urls) if d and d not in allowed}
        if suspicious:
            return ScamResult(True, f"Contains external domains/emails: {sorted(suspicious)[:3]}")

    return ScamResult(False, "")

