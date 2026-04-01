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
class NaukriScraperSource:
    name: str
    query: str
    location: str = ""
    pages: int = 1

    def fetch(self) -> list[Job]:
        jobs: list[Job] = []
        q = quote_plus(self.query or "")
        loc = quote_plus(self.location or "")
        pages = max(1, min(int(self.pages), 5))

        for page in range(1, pages + 1):
            # Best-effort public search URL.
            if loc:
                url = f"https://www.naukri.com/{q}-jobs-in-{loc}-{page}"
            else:
                url = f"https://www.naukri.com/{q}-jobs-{page}"

            try:
                resp = get(url, headers={"Accept": "text/html,application/xhtml+xml"})
            except requests.RequestException:
                # Naukri often blocks bots with 403; skip quietly.
                continue
            soup = BeautifulSoup(resp.text, "html.parser")

            cards = soup.select("article.jobTuple") or soup.select("div.srp-jobtuple-wrapper")
            for c in cards:
                title_el = c.select_one("a.title")
                company_el = c.select_one("a.comp-name") or c.select_one("a.subTitle")
                loc_el = c.select_one("span.locWdth") or c.select_one("li.location")
                exp_el = c.select_one("span.expwdth") or c.select_one("li.experience")

                title = normalize_text(title_el.get_text(" ", strip=True) if title_el else "")
                href = normalize_text(title_el.get("href") if title_el else "")
                company = normalize_text(company_el.get_text(" ", strip=True) if company_el else "Unknown")
                location = normalize_text(loc_el.get_text(" ", strip=True) if loc_el else "Unknown")
                exp = normalize_text(exp_el.get_text(" ", strip=True) if exp_el else "")
                desc = normalize_text(c.get_text(" ", strip=True))
                if exp:
                    desc = (desc + " | experience: " + exp).strip()

                if not title or not href:
                    continue

                jobs.append(
                    Job(
                        source="naukri_scraper",
                        title=title,
                        company=company,
                        location=location,
                        salary=None,
                        url=href,
                        description=desc,
                        posted_at=datetime.utcnow(),
                    )
                )

        return jobs

