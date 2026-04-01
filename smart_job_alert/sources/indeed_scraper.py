from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from urllib.parse import quote_plus

from bs4 import BeautifulSoup
import requests

from ..http import get
from ..models import Job
from ..text_utils import normalize_text


@dataclass
class IndeedScraperSource:
    name: str
    query: str
    location: str = ""
    pages: int = 1

    def fetch(self) -> list[Job]:
        jobs: list[Job] = []
        q = quote_plus(self.query or "")
        l = quote_plus(self.location or "")
        pages = max(1, min(int(self.pages), 5))

        for page in range(pages):
            start = page * 10
            url = f"https://in.indeed.com/jobs?q={q}&l={l}&start={start}"
            try:
                resp = get(url, headers={"Accept": "text/html,application/xhtml+xml"})
            except requests.RequestException:
                # Indeed often blocks bots with 403; skip quietly.
                continue
            soup = BeautifulSoup(resp.text, "html.parser")

            cards = soup.select("div.job_seen_beacon, div.cardOutline")
            for c in cards:
                title_el = c.select_one("h2.jobTitle a span") or c.select_one("h2.jobTitle span") or c.select_one("h2 a")
                company_el = c.select_one("[data-testid='company-name']") or c.select_one("span.companyName")
                loc_el = c.select_one("[data-testid='text-location']") or c.select_one("div.companyLocation")
                link_el = c.select_one("h2.jobTitle a") or c.select_one("a.jcs-JobTitle")
                salary_el = c.select_one("div.metadata.salary-snippet-container") or c.select_one("span.salary-snippet")

                title = normalize_text(title_el.get_text(" ", strip=True) if title_el else "")
                company = normalize_text(company_el.get_text(" ", strip=True) if company_el else "Unknown")
                location = normalize_text(loc_el.get_text(" ", strip=True) if loc_el else "Unknown")
                href = (link_el.get("href") if link_el else "") or ""
                salary = normalize_text(salary_el.get_text(" ", strip=True) if salary_el else "") or None

                if href.startswith("/"):
                    href = "https://in.indeed.com" + href

                if not title or not href:
                    continue

                desc = normalize_text(c.get_text(" ", strip=True))
                jobs.append(
                    Job(
                        source="indeed_scraper",
                        title=title,
                        company=company,
                        location=location,
                        salary=salary,
                        url=href,
                        description=desc,
                        posted_at=datetime.utcnow(),
                    )
                )

        return jobs

