from __future__ import annotations

from typing import Any

from ..config import SourceConfig
from .foundit_scraper import FounditScraperSource
from .indeed_scraper import IndeedScraperSource
from .internshala_scraper import InternshalaScraperSource
from .linkedin_jobs import LinkedInJobsSource
from .naukri_scraper import NaukriScraperSource
from .remotive_api import RemotiveAPISource
from .rss import RSSFeed, RSSSource


def build_source(sc: SourceConfig):
    t = sc.type.strip().lower()
    opts: dict[str, Any] = sc.options or {}

    if t == "remotive_api":
        return RemotiveAPISource(name=sc.name, query=str(opts.get("query", "") or ""), category=str(opts.get("category", "") or ""))

    if t == "rss":
        feeds_raw = ((opts.get("feeds") or []) if isinstance(opts, dict) else []) or []
        feeds = []
        for f in feeds_raw:
            if not isinstance(f, dict):
                continue
            url = str(f.get("url", "") or "").strip()
            if not url:
                continue
            feeds.append(
                RSSFeed(
                    name=str(f.get("name", "feed") or "feed"),
                    url=url,
                    source_name=str(f.get("source_name", "rss") or "rss"),
                )
            )
        return RSSSource(name=sc.name, feeds=feeds)

    if t == "indeed_scraper":
        return IndeedScraperSource(
            name=sc.name,
            query=str(opts.get("query", "") or ""),
            location=str(opts.get("location", "") or ""),
            pages=int(opts.get("pages", 1) or 1),
        )

    if t == "naukri_scraper":
        return NaukriScraperSource(
            name=sc.name,
            query=str(opts.get("query", "") or ""),
            location=str(opts.get("location", "") or ""),
            pages=int(opts.get("pages", 1) or 1),
        )

    if t == "linkedin_jobs":
        return LinkedInJobsSource(
            name=sc.name,
            query=str(opts.get("query", "") or ""),
            location=str(opts.get("location", "") or ""),
            pages=int(opts.get("pages", 1) or 1),
        )

    if t == "internshala_scraper":
        return InternshalaScraperSource(
            name=sc.name,
            query=str(opts.get("query", "") or ""),
            pages=int(opts.get("pages", 1) or 1),
        )

    if t == "foundit_scraper":
        return FounditScraperSource(
            name=sc.name,
            query=str(opts.get("query", "") or ""),
            location=str(opts.get("location", "india") or "india"),
            pages=int(opts.get("pages", 1) or 1),
        )

    raise ValueError(f"Unknown source type: {sc.type}")

