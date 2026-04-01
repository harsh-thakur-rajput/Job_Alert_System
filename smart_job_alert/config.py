from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml


@dataclass
class TelegramConfig:
    enabled: bool = False
    bot_token: str = ""
    chat_id: str = ""


@dataclass
class EmailConfig:
    enabled: bool = False
    smtp_host: str = ""
    smtp_port: int = 587
    username: str = ""
    password: str = ""
    from_addr: str = ""
    to_addrs: list[str] = None  # type: ignore[assignment]
    use_starttls: bool = True

    def __post_init__(self) -> None:
        if self.to_addrs is None:
            self.to_addrs = []


@dataclass
class FiltersConfig:
    keywords: list[str]
    experience_max_years: float = 1.0
    locations_allow: list[str] = None  # type: ignore[assignment]
    keywords_exclude: list[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.locations_allow is None:
            self.locations_allow = []
        if self.keywords_exclude is None:
            self.keywords_exclude = []


@dataclass
class ScamConfig:
    enabled: bool = True
    allowed_domains: list[str] = None  # type: ignore[assignment]
    blocked_domains: list[str] = None  # type: ignore[assignment]
    payment_keywords: list[str] = None  # type: ignore[assignment]
    min_description_chars: int = 120

    def __post_init__(self) -> None:
        if self.allowed_domains is None:
            self.allowed_domains = []
        if self.blocked_domains is None:
            self.blocked_domains = []
        if self.payment_keywords is None:
            self.payment_keywords = [
                "registration fee",
                "pay to apply",
                "processing fee",
                "training fee",
                "deposit",
                "payable",
                "upi",
                "paytm",
            ]


@dataclass
class RankingConfig:
    min_score_to_alert: float = 0.35
    max_jobs_per_alert: int = 10
    prefer_salary: bool = True
    prefer_recent_days: int = 14


@dataclass
class SchedulerConfig:
    enabled: bool = True
    interval_hours: int = 8


@dataclass
class DatabaseConfig:
    path: str = "jobs.db"


@dataclass
class SourceConfig:
    type: str
    name: str
    enabled: bool = True
    options: dict[str, Any] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.options is None:
            self.options = {}


@dataclass
class AppConfig:
    sources: list[SourceConfig]
    filters: FiltersConfig
    scam: ScamConfig = field(default_factory=ScamConfig)
    ranking: RankingConfig = field(default_factory=RankingConfig)
    scheduler: SchedulerConfig = field(default_factory=SchedulerConfig)
    telegram: TelegramConfig = field(default_factory=TelegramConfig)
    email: EmailConfig = field(default_factory=EmailConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    log_level: str = "INFO"
    user_profile_path: str = "user_profile.json"


def _coalesce(d: dict[str, Any], key: str, default: Any) -> Any:
    v = d.get(key, default)
    return default if v is None else v


def load_config(path: str | Path) -> AppConfig:
    path = Path(path)
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    sources = [
        SourceConfig(
            type=s["type"],
            name=s.get("name", s["type"]),
            enabled=bool(s.get("enabled", True)),
            options=dict(s.get("options", {}) or {}),
        )
        for s in (raw.get("sources", []) or [])
    ]
    if not sources:
        raise ValueError("No sources configured. Run `init-config` to generate a starter config.yaml.")

    filters_raw = raw.get("filters", {}) or {}
    filters = FiltersConfig(
        keywords=list(filters_raw.get("keywords", []) or []),
        experience_max_years=float(_coalesce(filters_raw, "experience_max_years", 1.0)),
        locations_allow=list(filters_raw.get("locations_allow", []) or []),
        keywords_exclude=list(filters_raw.get("keywords_exclude", []) or []),
    )
    if not filters.keywords:
        raise ValueError("filters.keywords is required (e.g. ['Python Developer']).")

    scam_raw = raw.get("scam", {}) or {}
    scam = ScamConfig(
        enabled=bool(_coalesce(scam_raw, "enabled", True)),
        allowed_domains=list(scam_raw.get("allowed_domains", []) or []),
        blocked_domains=list(scam_raw.get("blocked_domains", []) or []),
        payment_keywords=list(scam_raw.get("payment_keywords", None) or []) or None,
        min_description_chars=int(_coalesce(scam_raw, "min_description_chars", 120)),
    )

    ranking_raw = raw.get("ranking", {}) or {}
    ranking = RankingConfig(
        min_score_to_alert=float(_coalesce(ranking_raw, "min_score_to_alert", 0.35)),
        max_jobs_per_alert=int(_coalesce(ranking_raw, "max_jobs_per_alert", 10)),
        prefer_salary=bool(_coalesce(ranking_raw, "prefer_salary", True)),
        prefer_recent_days=int(_coalesce(ranking_raw, "prefer_recent_days", 14)),
    )

    sched_raw = raw.get("scheduler", {}) or {}
    scheduler = SchedulerConfig(
        enabled=bool(_coalesce(sched_raw, "enabled", True)),
        interval_hours=int(_coalesce(sched_raw, "interval_hours", 8)),
    )

    telegram_raw = raw.get("telegram", {}) or {}
    telegram = TelegramConfig(
        enabled=bool(_coalesce(telegram_raw, "enabled", False)),
        bot_token=str(_coalesce(telegram_raw, "bot_token", "")),
        chat_id=str(_coalesce(telegram_raw, "chat_id", "")),
    )

    email_raw = raw.get("email", {}) or {}
    email = EmailConfig(
        enabled=bool(_coalesce(email_raw, "enabled", False)),
        smtp_host=str(_coalesce(email_raw, "smtp_host", "")),
        smtp_port=int(_coalesce(email_raw, "smtp_port", 587)),
        username=str(_coalesce(email_raw, "username", "")),
        password=str(_coalesce(email_raw, "password", "")),
        from_addr=str(_coalesce(email_raw, "from_addr", "")),
        to_addrs=list(email_raw.get("to_addrs", []) or []),
        use_starttls=bool(_coalesce(email_raw, "use_starttls", True)),
    )

    db_raw = raw.get("database", {}) or {}
    database = DatabaseConfig(path=str(_coalesce(db_raw, "path", "jobs.db")))

    return AppConfig(
        sources=sources,
        filters=filters,
        scam=scam,
        ranking=ranking,
        scheduler=scheduler,
        telegram=telegram,
        email=email,
        database=database,
        log_level=str(_coalesce(raw, "log_level", "INFO")),
        user_profile_path=str(_coalesce(raw, "user_profile_path", "user_profile.json")),
    )


def write_default_config(path: str | Path) -> None:
    path = Path(path)
    if path.exists():
        raise FileExistsError(f"{path} already exists")

    starter = {
        "log_level": "INFO",
        "database": {"path": "jobs.db"},
        "user_profile_path": "user_profile.json",
        "filters": {
            "keywords": ["Python Developer", "Software Engineer"],
            "keywords_exclude": ["senior", "lead", "manager"],
            "experience_max_years": 1.0,
            "locations_allow": ["India", "Remote", "Bengaluru", "Hyderabad", "Pune"],
        },
        "scam": {
            "enabled": True,
            "allowed_domains": [],
            "blocked_domains": [],
            "min_description_chars": 120,
            "payment_keywords": [
                "registration fee",
                "pay to apply",
                "processing fee",
                "training fee",
                "deposit",
                "upi",
                "paytm",
            ],
        },
        "ranking": {"min_score_to_alert": 0.35, "max_jobs_per_alert": 10, "prefer_salary": True, "prefer_recent_days": 14},
        "scheduler": {"enabled": True, "interval_hours": 8},
        "telegram": {"enabled": False, "bot_token": "", "chat_id": ""},
        "email": {
            "enabled": False,
            "smtp_host": "",
            "smtp_port": 587,
            "username": "",
            "password": "",
            "from_addr": "",
            "to_addrs": [],
            "use_starttls": True,
        },
        "sources": [
            {
                "type": "remotive_api",
                "name": "Remotive",
                "enabled": True,
                "options": {"query": "python", "category": "software-dev"},
            },
            {
                "type": "rss",
                "name": "Indeed RSS (example)",
                "enabled": False,
                "options": {
                    "feeds": [
                        {
                            "name": "Indeed Python",
                            "url": "https://www.indeed.com/jobs?q=python&sort=date&fromage=3&rss=1",
                            "source_name": "indeed_rss",
                        }
                    ]
                },
            },
        ],
    }
    path.write_text(yaml.safe_dump(starter, sort_keys=False, allow_unicode=True), encoding="utf-8")

