from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

import requests

from .config import EmailConfig, TelegramConfig


log = logging.getLogger(__name__)


def format_job_line(job_row) -> str:  # type: ignore[no-untyped-def]
    title = job_row["title"]
    company = job_row["company"]
    location = job_row["location"]
    score = job_row["score"]
    url = job_row["url"]
    return f"- {title} @ {company} ({location}) | score={score:.2f}\n  {url}"


def build_digest(job_rows: list) -> str:  # type: ignore[type-arg]
    lines = [f"Smart Job Alert: {len(job_rows)} new matches"]
    for r in job_rows:
        lines.append(format_job_line(r))
    return "\n".join(lines).strip()


def send_telegram(cfg: TelegramConfig, text: str) -> None:
    if not cfg.enabled:
        return
    if not cfg.bot_token or not cfg.chat_id:
        raise ValueError("Telegram enabled but bot_token/chat_id missing in config")
    url = f"https://api.telegram.org/bot{cfg.bot_token}/sendMessage"
    payload = {
        "chat_id": cfg.chat_id,
        "text": text,
        "disable_web_page_preview": True,
    }
    resp = requests.post(url, data=payload, timeout=25)
    resp.raise_for_status()


def send_email(cfg: EmailConfig, subject: str, body: str) -> None:
    if not cfg.enabled:
        return
    if not cfg.smtp_host or not cfg.from_addr or not cfg.to_addrs:
        raise ValueError("Email enabled but smtp_host/from_addr/to_addrs missing in config")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = cfg.from_addr
    msg["To"] = ", ".join(cfg.to_addrs)
    msg.set_content(body)

    with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port, timeout=30) as s:
        if cfg.use_starttls:
            s.starttls()
        if cfg.username:
            s.login(cfg.username, cfg.password)
        s.send_message(msg)


def send_alerts(*, telegram: TelegramConfig, email: EmailConfig, job_rows: list) -> None:  # type: ignore[type-arg]
    if not job_rows:
        return
    text = build_digest(job_rows)
    if telegram.enabled:
        log.info("Sending Telegram alert (%d jobs)", len(job_rows))
        send_telegram(telegram, text)
    if email.enabled:
        log.info("Sending Email alert (%d jobs)", len(job_rows))
        send_email(email, subject="Smart Job Alert", body=text)

