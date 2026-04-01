from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from bs4 import BeautifulSoup
from dateutil import parser as date_parser

from ..http import get
from ..models import Job
from ..text_utils import normalize_text


@dataclass
class RSSFeed:
    name: str
    url: str
    source_name: str = "rss"


@dataclass
class RSSSource:
    name: str
    feeds: list[RSSFeed]

    def fetch(self) -> list[Job]:
        jobs: list[Job] = []
        for feed in self.feeds:
            resp = get(feed.url, headers={"Accept": "application/rss+xml,application/xml,text/xml;q=0.9,*/*;q=0.8"})
            soup = BeautifulSoup(resp.text, "xml")
            items = soup.find_all("item")
            for it in items:
                title = normalize_text(it.title.get_text(" ", strip=True) if it.title else "")
                link = normalize_text(it.link.get_text(" ", strip=True) if it.link else "")
                desc = normalize_text(it.description.get_text(" ", strip=True) if it.description else "")
                company = ""
                location = ""

                # Best-effort extraction from common RSS patterns.
                if it.find("source"):
                    company = normalize_text(it.find("source").get_text(" ", strip=True))
                if it.find("author"):
                    company = company or normalize_text(it.find("author").get_text(" ", strip=True))

                if " - " in title and not company:
                    # Many feeds format: "Job title - Company"
                    parts = [p.strip() for p in title.split(" - ", 1)]
                    if len(parts) == 2:
                        title, company = parts[0], parts[1]

                posted_at: Optional[datetime] = None
                try:
                    pub = it.pubDate.get_text(" ", strip=True) if it.pubDate else ""
                    if pub:
                        posted_at = date_parser.parse(pub)
                except Exception:
                    posted_at = None

                if not title or not link:
                    continue

                jobs.append(
                    Job(
                        source=feed.source_name or "rss",
                        title=title,
                        company=company or "Unknown",
                        location=location or "Unknown",
                        url=link,
                        description=desc,
                        posted_at=posted_at,
                        external_id=None,
                    )
                )
        return jobs

