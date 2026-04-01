from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from ..http import get
from ..models import Job
from ..text_utils import normalize_text


@dataclass
class LinkedInJobsSource:
    name: str
    query: str
    location: str = ""
    pages: int = 1

    def fetch(self) -> list[Job]:
        jobs: list[Job] = []
        q = quote_plus(self.query or "")
        loc = quote_plus(self.location or "")
        pages = max(1, min(int(self.pages), 5))

        for p in range(pages):
            start = p * 25
            url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={q}&location={loc}&start={start}"
            resp = get(url, headers={"Accept": "text/html,application/xhtml+xml"})
            soup = BeautifulSoup(resp.text, "html.parser")

            cards = soup.select("li")
            for c in cards:
                title_el = c.select_one("h3.base-search-card__title")
                company_el = c.select_one("h4.base-search-card__subtitle")
                loc_el = c.select_one("span.job-search-card__location")
                link_el = c.select_one("a.base-card__full-link")
                time_el = c.select_one("time")

                title = normalize_text(title_el.get_text(" ", strip=True) if title_el else "")
                company = normalize_text(company_el.get_text(" ", strip=True) if company_el else "Unknown")
                location = normalize_text(loc_el.get_text(" ", strip=True) if loc_el else "Unknown")
                href = normalize_text(link_el.get("href") if link_el else "")
                desc = normalize_text(c.get_text(" ", strip=True))

                posted_at = None
                if time_el and time_el.has_attr("datetime"):
                    try:
                        posted_at = datetime.fromisoformat(str(time_el["datetime"]))
                    except Exception:
                        posted_at = datetime.utcnow()
                else:
                    posted_at = datetime.utcnow()

                if not title or not href:
                    continue

                jobs.append(
                    Job(
                        source="linkedin_jobs",
                        title=title,
                        company=company,
                        location=location,
                        salary=None,
                        url=href,
                        description=desc,
                        posted_at=posted_at,
                    )
                )
        return jobs

