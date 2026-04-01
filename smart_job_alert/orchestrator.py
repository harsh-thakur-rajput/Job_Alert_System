from __future__ import annotations

import logging
from dataclasses import dataclass

from .alerts import send_alerts
from .config import AppConfig
from .db import JobStore
from .filters import pass_user_filters
from .learn import train_optional_sklearn_model
from .ranking import base_score, combine_scores, try_learned_score
from .scam import detect_scam
from .sources.factory import build_source
from .text_utils import normalize_text


log = logging.getLogger(__name__)


@dataclass(frozen=True)
class RunStats:
    fetched: int
    kept_after_filters: int
    inserted: int
    alerted: int
    scams: int


def _job_to_text(job) -> str:  # type: ignore[no-untyped-def]
    return " | ".join(
        [
            normalize_text(job.title),
            normalize_text(job.company),
            normalize_text(job.location),
            normalize_text(job.description),
        ]
    ).strip()


def run_once(cfg: AppConfig) -> RunStats:
    with JobStore(cfg.database.path) as store:
        sources = [build_source(s) for s in cfg.sources if s.enabled]
        log.info("Enabled sources: %s", ", ".join(getattr(s, "name", "source") for s in sources))

        fetched_jobs = []
        for src in sources:
            try:
                batch = src.fetch()
                log.info("Fetched %d from %s", len(batch), getattr(src, "name", "source"))
                fetched_jobs.extend(batch)
            except Exception as e:
                log.exception("Source failed (%s): %s", getattr(src, "name", "source"), e)

        fetched = len(fetched_jobs)

        # Dedupe early by URL hash (cheap) and DB "seen" check.
        unseen_jobs = []
        seen_hashes: set[str] = set()
        for j in fetched_jobs:
            h = store.url_hash(j.url)
            if h in seen_hashes:
                continue
            seen_hashes.add(h)
            if store.has_seen(j.url):
                continue
            unseen_jobs.append(j)

        # Apply user filters.
        filtered = [
            j
            for j in unseen_jobs
            if pass_user_filters(
                j,
                keywords=cfg.filters.keywords,
                keywords_exclude=cfg.filters.keywords_exclude,
                locations_allow=cfg.filters.locations_allow,
                experience_max_years=cfg.filters.experience_max_years,
            )
        ]

        # Optional preference learning from feedback (if sklearn available).
        training = store.get_feedback_training_rows()
        model = train_optional_sklearn_model(training)
        if model:
            log.info("Preference model trained on %d feedback rows", len(training))

        scores: dict[str, float] = {}
        scam_flags: dict[str, tuple[bool, str]] = {}

        scams = 0
        for j in filtered:
            h = store.url_hash(j.url)

            scam_res = detect_scam(
                j,
                allowed_domains=cfg.scam.allowed_domains,
                blocked_domains=cfg.scam.blocked_domains,
                payment_keywords=cfg.scam.payment_keywords,
                min_description_chars=cfg.scam.min_description_chars,
            ) if cfg.scam.enabled else None

            if scam_res and scam_res.is_scam:
                scams += 1
                scam_flags[h] = (True, scam_res.reason)
            else:
                scam_flags[h] = (False, "")

            b, b_reasons = base_score(
                j,
                keywords=cfg.filters.keywords,
                prefer_salary=cfg.ranking.prefer_salary,
                prefer_recent_days=cfg.ranking.prefer_recent_days,
            )
            learned = try_learned_score(_job_to_text(j), model.pipeline if model else None)
            combined, l_reasons = combine_scores(b, learned)
            scores[h] = combined

        inserted = store.insert_jobs(filtered, scores=scores, scam_flags=scam_flags)

        # Smart alert: only the jobs from this run, sorted by score, excluding scams.
        candidates = []
        for j in filtered:
            h = store.url_hash(j.url)
            if scam_flags.get(h, (False, ""))[0]:
                continue
            candidates.append((scores.get(h, 0.0), j))

        candidates.sort(key=lambda x: x[0], reverse=True)
        top = [j for s, j in candidates if s >= cfg.ranking.min_score_to_alert][: cfg.ranking.max_jobs_per_alert]

        # Convert to dict-like rows for alert formatting.
        job_rows = [
            {
                "title": j.title,
                "company": j.company,
                "location": j.location,
                "url": j.url,
                "score": float(scores.get(store.url_hash(j.url), 0.0)),
            }
            for j in top
        ]

        send_alerts(telegram=cfg.telegram, email=cfg.email, job_rows=job_rows)

        alerted = len(job_rows)
        log.info(
            "Run complete: fetched=%d unseen=%d filtered=%d inserted=%d scams=%d alerted=%d",
            fetched,
            len(unseen_jobs),
            len(filtered),
            inserted,
            scams,
            alerted,
        )

        return RunStats(
            fetched=fetched,
            kept_after_filters=len(filtered),
            inserted=inserted,
            alerted=alerted,
            scams=scams,
        )

