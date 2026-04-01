from __future__ import annotations

from typing import Protocol

from ..models import Job


class JobSource(Protocol):
    name: str

    def fetch(self) -> list[Job]:
        ...

