from __future__ import annotations

from typing import Any, Optional

import requests
from tenacity import retry, stop_after_attempt, wait_exponential


DEFAULT_HEADERS = {
    "User-Agent": "smart-job-alert/0.1 (+https://example.invalid)",
    "Accept": "application/json,text/html,application/rss+xml,application/xml;q=0.9,*/*;q=0.8",
}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
def get(url: str, *, timeout_s: int = 20, headers: Optional[dict[str, str]] = None) -> requests.Response:
    h = dict(DEFAULT_HEADERS)
    if headers:
        h.update(headers)
    resp = requests.get(url, timeout=timeout_s, headers=h)
    resp.raise_for_status()
    return resp


def get_json(url: str, *, timeout_s: int = 20) -> Any:
    resp = get(url, timeout_s=timeout_s, headers={"Accept": "application/json"})
    return resp.json()

