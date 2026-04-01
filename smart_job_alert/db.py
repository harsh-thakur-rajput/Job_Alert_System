from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

from .models import Job


SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT NOT NULL,
  external_id TEXT,
  url TEXT NOT NULL,
  url_hash TEXT NOT NULL,
  title TEXT NOT NULL,
  company TEXT NOT NULL,
  location TEXT NOT NULL,
  salary TEXT,
  description TEXT,
  posted_at TEXT,
  scraped_at TEXT NOT NULL,
  score REAL,
  is_scam INTEGER DEFAULT 0,
  scam_reason TEXT,
  created_at TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_jobs_url_hash ON jobs(url_hash);

CREATE TABLE IF NOT EXISTS feedback (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  url_hash TEXT NOT NULL,
  label INTEGER NOT NULL, -- 1 liked, 0 disliked
  created_at TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_feedback_url_hash ON feedback(url_hash);
"""


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


class JobStore:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "JobStore":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
        self.close()

    def url_hash(self, url: str) -> str:
        return _sha256(url.strip())

    def has_seen(self, url: str) -> bool:
        h = self.url_hash(url)
        cur = self._conn.execute("SELECT 1 FROM jobs WHERE url_hash = ? LIMIT 1", (h,))
        return cur.fetchone() is not None

    def insert_jobs(
        self,
        jobs: Iterable[Job],
        *,
        scores: Optional[dict[str, float]] = None,
        scam_flags: Optional[dict[str, tuple[bool, str]]] = None,
    ) -> int:
        scores = scores or {}
        scam_flags = scam_flags or {}

        inserted = 0
        now = datetime.utcnow().isoformat()
        for job in jobs:
            d = asdict(job)
            url = d["url"]
            h = self.url_hash(url)
            score = float(scores.get(h, 0.0))
            is_scam, scam_reason = scam_flags.get(h, (False, ""))
            try:
                self._conn.execute(
                    """
                    INSERT INTO jobs
                    (source, external_id, url, url_hash, title, company, location, salary, description, posted_at, scraped_at, score, is_scam, scam_reason, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        d["source"],
                        d["external_id"],
                        url,
                        h,
                        d["title"],
                        d["company"],
                        d["location"],
                        d["salary"],
                        d["description"],
                        d["posted_at"].isoformat() if d["posted_at"] else None,
                        d["scraped_at"].isoformat(),
                        score,
                        1 if is_scam else 0,
                        scam_reason,
                        now,
                    ),
                )
                inserted += 1
            except sqlite3.IntegrityError:
                continue
        self._conn.commit()
        return inserted

    def get_unalerted_candidates(self, *, min_score: float, limit: int) -> list[sqlite3.Row]:
        # "Smart alerts" here means: only send **new** rows and don't resend.
        # We track this implicitly by using created_at within the last run window in orchestrator.
        cur = self._conn.execute(
            """
            SELECT * FROM jobs
            WHERE is_scam = 0 AND score >= ?
            ORDER BY score DESC, scraped_at DESC
            LIMIT ?
            """,
            (min_score, limit),
        )
        return list(cur.fetchall())

    def upsert_feedback(self, url: str, liked: bool) -> None:
        h = self.url_hash(url)
        now = datetime.utcnow().isoformat()
        self._conn.execute(
            """
            INSERT INTO feedback (url_hash, label, created_at)
            VALUES (?, ?, ?)
            ON CONFLICT(url_hash) DO UPDATE SET label=excluded.label, created_at=excluded.created_at
            """,
            (h, 1 if liked else 0, now),
        )
        self._conn.commit()

    def get_feedback_training_rows(self, *, limit: int = 2000) -> list[tuple[str, int]]:
        cur = self._conn.execute(
            """
            SELECT j.title, j.company, j.location, j.description, f.label
            FROM feedback f
            JOIN jobs j ON j.url_hash = f.url_hash
            ORDER BY f.created_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = []
        for r in cur.fetchall():
            text = " | ".join([r["title"] or "", r["company"] or "", r["location"] or "", r["description"] or ""]).strip()
            rows.append((text, int(r["label"])))
        return rows

