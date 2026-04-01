from __future__ import annotations

import re

from .models import Job
from .text_utils import contains_any, normalize_text


_EXP_RE = re.compile(r"(\d+)\s*[-–to]+\s*(\d+)\s*(?:years|yrs)\b", re.IGNORECASE)
_EXP_SINGLE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:years|yrs)\b", re.IGNORECASE)


def parse_experience_years(text: str) -> tuple[float | None, float | None]:
    t = (text or "").lower()
    m = _EXP_RE.search(t)
    if m:
        return float(m.group(1)), float(m.group(2))
    m2 = _EXP_SINGLE_RE.search(t)
    if m2:
        v = float(m2.group(1))
        return v, v
    return None, None


def pass_user_filters(
    job: Job,
    *,
    keywords: list[str],
    keywords_exclude: list[str],
    locations_allow: list[str],
    experience_max_years: float,
) -> bool:
    title = normalize_text(job.title)
    company = normalize_text(job.company)
    location = normalize_text(job.location)
    desc = normalize_text(job.description)
    hay = " | ".join([title, company, location, desc])

    if keywords and not contains_any(hay, keywords):
        return False
    if keywords_exclude and contains_any(hay, keywords_exclude):
        return False
    if locations_allow and not contains_any(location, locations_allow):
        return False

    lo, hi = parse_experience_years(hay)
    if hi is not None and hi > experience_max_years:
        return False
    if lo is not None and lo > experience_max_years:
        return False
    return True

