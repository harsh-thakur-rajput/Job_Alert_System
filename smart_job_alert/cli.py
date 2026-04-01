from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .config import load_config, write_default_config
from .db import JobStore
from .logging_utils import setup_logging
from .orchestrator import run_once
from .scheduler import run_scheduler


log = logging.getLogger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="smart-job-alert", description="Smart Job Alert System")
    sub = p.add_subparsers(dest="cmd", required=True)

    initp = sub.add_parser("init-config", help="Create a starter config.yaml")
    initp.add_argument("--path", default="config.yaml", help="Output path (default: config.yaml)")

    runp = sub.add_parser("run-once", help="Fetch, filter, rank, store, and alert once")
    runp.add_argument("--config", default="config.yaml", help="Path to config.yaml")

    schedp = sub.add_parser("run-scheduler", help="Run automatically every N hours")
    schedp.add_argument("--config", default="config.yaml", help="Path to config.yaml")

    fb = sub.add_parser("feedback", help="Label a job as liked/disliked (improves ranking over time)")
    fb.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    fb.add_argument("--url", required=True, help="Job URL to label")
    fb.add_argument("--liked", action="store_true", help="Mark as liked")
    fb.add_argument("--disliked", action="store_true", help="Mark as disliked")

    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    if args.cmd == "init-config":
        out = Path(args.path)
        write_default_config(out)
        print(f"Wrote {out}")  # noqa: T201
        return 0

    cfg = load_config(args.config)
    setup_logging(cfg.log_level)

    if args.cmd == "run-once":
        stats = run_once(cfg)
        print(stats)  # noqa: T201
        return 0

    if args.cmd == "run-scheduler":
        run_scheduler(cfg)
        return 0

    if args.cmd == "feedback":
        if bool(args.liked) == bool(args.disliked):
            raise SystemExit("Provide exactly one of --liked or --disliked")
        with JobStore(cfg.database.path) as store:
            store.upsert_feedback(args.url, liked=bool(args.liked))
        print("Saved feedback")  # noqa: T201
        return 0

    raise SystemExit(f"Unknown command: {args.cmd}")

