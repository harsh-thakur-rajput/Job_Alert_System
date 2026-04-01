from __future__ import annotations

import logging
import time

from apscheduler.schedulers.background import BackgroundScheduler

from .config import AppConfig
from .orchestrator import run_once


log = logging.getLogger(__name__)


def run_scheduler(cfg: AppConfig) -> None:
    if not cfg.scheduler.enabled:
        raise ValueError("scheduler.enabled is false in config")

    interval_h = int(cfg.scheduler.interval_hours)
    if interval_h <= 0:
        raise ValueError("scheduler.interval_hours must be > 0")

    sched = BackgroundScheduler()
    sched.add_job(lambda: run_once(cfg), "interval", hours=interval_h, id="job_alert_run")
    sched.start()

    log.info("Scheduler started. Interval=%dh. Press Ctrl+C to stop.", interval_h)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("Stopping scheduler...")
        sched.shutdown(wait=False)

