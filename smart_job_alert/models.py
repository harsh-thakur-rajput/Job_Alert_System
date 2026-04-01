from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class Job:
    source: str
    title: str
    company: str
    location: str
    url: str
    description: str = ""
    salary: Optional[str] = None
    posted_at: Optional[datetime] = None
    external_id: Optional[str] = None
    scraped_at: datetime = field(default_factory=datetime.utcnow)

