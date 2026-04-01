from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from dateutil import parser as date_parser

from ..http import get_json
from ..models import Job
from ..text_utils import normalize_text


@dataclass
class RemotiveAPISource:
    name: str
    query: str = ""
    category: str = ""

    def fetch(self) -> list[Job]:
        url = "https://remotive.com/api/remote-jobs"
        params = []
        if self.query:
            params.append(f"search={self.query}")
        if self.category:
            params.append(f"category={self.category}")
        if params:
            url = url + "?" + "&".join(params)

        data: Any = get_json(url)
        items = data.get("jobs", []) or []
        jobs: list[Job] = []
        for it in items:
            title = normalize_text(str(it.get("title", "") or ""))
            company = normalize_text(str(it.get("company_name", "") or ""))
            location = normalize_text(str(it.get("candidate_required_location", "") or "Remote"))
            job_url = str(it.get("url", "") or "")
            desc = normalize_text(str(it.get("description", "") or ""))
            salary = normalize_text(str(it.get("salary", "") or "")) or None

            posted_at: Optional[datetime] = None
            try:
                if it.get("publication_date"):
                    posted_at = date_parser.isoparse(str(it["publication_date"]))
            except Exception:
                posted_at = None

            external_id = str(it.get("id", "") or "") or None

            if not title or not company or not job_url:
                continue

            jobs.append(
                Job(
                    source="remotive_api",
                    title=title,
                    company=company,
                    location=location,
                    salary=salary,
                    url=job_url,
                    description=desc,
                    posted_at=posted_at,
                    external_id=external_id,
                )
            )
        return jobs

