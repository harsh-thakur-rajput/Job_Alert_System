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
class InternshalaScraperSource:
    name: str
    query: str
    pages: int = 1

    def fetch(self) -> list[Job]:
        jobs: list[Job] = []
        q = quote_plus(self.query or "")
        pages = max(1, min(int(self.pages), 3))

        for p in range(1, pages + 1):
            suffix = "" if p == 1 else f"/page-{p}"
            url = f"https://internshala.com/jobs/keywords-{q}{suffix}"
            try:
                resp = get(url, headers={"Accept": "text/html,application/xhtml+xml"})
            except requests.RequestException:
                continue

            soup = BeautifulSoup(resp.text, "html.parser")
            cards = soup.select("div.individual_internship") or soup.select("div.container-fluid.individual_internship")
            for c in cards:
                title_el = c.select_one("h3.job-internship-name a") or c.select_one("a.job-title-href")
                company_el = c.select_one("p.company-name") or c.select_one("p.company_and_premium span")
                loc_el = c.select_one("div.row-1-item.locations span")
                link_el = c.select_one("h3.job-internship-name a") or c.select_one("a.job-title-href")
                stipend_el = c.select_one("span.stipend")

                title = normalize_text(title_el.get_text(" ", strip=True) if title_el else "")
                company = normalize_text(company_el.get_text(" ", strip=True) if company_el else "Unknown")
                location = normalize_text(loc_el.get_text(" ", strip=True) if loc_el else "India")
                href = (link_el.get("href") if link_el else "") or ""
                salary = normalize_text(stipend_el.get_text(" ", strip=True) if stipend_el else "") or None

                if href.startswith("/"):
                    href = "https://internshala.com" + href

                if not title or not href:
                    continue

                desc = normalize_text(c.get_text(" ", strip=True))
                jobs.append(
                    Job(
                        source="internshala_scraper",
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

