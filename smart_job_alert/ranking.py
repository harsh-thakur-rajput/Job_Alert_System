from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from .models import Job
from .text_utils import keyword_count, normalize_text


@dataclass(frozen=True)
class RankedJob:
    job: Job
    score: float
    reasons: list[str]


def base_score(
    job: Job,
    *,
    keywords: list[str],
    prefer_salary: bool,
    prefer_recent_days: int,
) -> tuple[float, list[str]]:
    reasons: list[str] = []
    score = 0.0

    hay = " | ".join(
        [
            normalize_text(job.title),
            normalize_text(job.company),
            normalize_text(job.location),
            normalize_text(job.description),
        ]
    )

    k_hits = keyword_count(hay, keywords)
    if keywords:
        score += min(0.55, 0.18 * k_hits)
        if k_hits:
            reasons.append(f"keyword_hits={k_hits}")

    if prefer_salary and (job.salary and normalize_text(job.salary)):
        score += 0.08
        reasons.append("salary_present")

    if job.posted_at:
        days = (datetime.utcnow() - job.posted_at).days
        if days <= max(1, int(prefer_recent_days)):
            score += 0.12
            reasons.append("recent_post")
        else:
            score -= 0.05
            reasons.append("older_post")
    else:
        # Slight penalty if unknown; not fatal.
        score -= 0.02
        reasons.append("posted_at_unknown")

    # Clamp to [0,1]
    score = max(0.0, min(1.0, score))
    return score, reasons


def try_learned_score(text: str, model: Optional[object]) -> Optional[float]:
    if model is None:
        return None
    try:
        predict_proba = getattr(model, "predict_proba", None)
        if predict_proba is None:
            return None
        proba = predict_proba([text])
        # Expect shape (n,2) for [dislike, like]
        return float(proba[0][1])
    except Exception:
        return None


def combine_scores(base: float, learned: Optional[float]) -> tuple[float, list[str]]:
    reasons: list[str] = []
    if learned is None:
        return base, reasons
    # Weighted blend: base keeps system stable, learned nudges.
    score = 0.70 * base + 0.30 * max(0.0, min(1.0, learned))
    reasons.append("learned_preference")
    return max(0.0, min(1.0, score)), reasons

