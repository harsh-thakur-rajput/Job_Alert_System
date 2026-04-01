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
class FounditScraperSource:
    name: str
    query: str
    location: str = "india"
    pages: int = 1

    def fetch(self) -> list[Job]:
        jobs: list[Job] = []
        q = quote_plus(self.query or "")
        loc = quote_plus(self.location or "india")
        pages = max(1, min(int(self.pages), 3))

        for p in range(1, pages + 1):
            url = f"https://www.foundit.in/srp/results?query={q}&locations={loc}&page={p}"
            try:
                resp = get(url, headers={"Accept": "text/html,application/xhtml+xml"})
            except Exception:
                continue

            soup = BeautifulSoup(resp.text, "html.parser")
            cards = soup.select("div.srpResultCard") or soup.select("div.cardContainer")
            for c in cards:
                title_el = c.select_one("h3 a") or c.select_one("a[title]")
                company_el = c.select_one("div.companyName") or c.select_one("span.company")
                loc_el = c.select_one("div.locationDetails") or c.select_one("span.loc")
                link_el = title_el

                title = normalize_text(title_el.get_text(" ", strip=True) if title_el else "")
                company = normalize_text(company_el.get_text(" ", strip=True) if company_el else "Unknown")
                location = normalize_text(loc_el.get_text(" ", strip=True) if loc_el else "India")
                href = (link_el.get("href") if link_el else "") or ""

                if href.startswith("/"):
                    href = "https://www.foundit.in" + href

                if not title or not href:
                    continue

                desc = normalize_text(c.get_text(" ", strip=True))
                jobs.append(
                    Job(
                        source="foundit_scraper",
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

