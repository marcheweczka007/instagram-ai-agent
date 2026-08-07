"""Logging helpers shared across pipelines and the CLI."""

from __future__ import annotations

import logging
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from instagram_agent.config import get_settings


def setup_logging(level: str | None = None) -> None:
    """Configure root logging once for CLI and scripts."""
    settings = get_settings()
    settings.ensure_output_dirs()
    log_level = (level or settings.log_level).upper()

    root = logging.getLogger()
    if root.handlers:
        root.setLevel(log_level)
        return

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(
                settings.logs_dir / "instagram_agent.log",
                encoding="utf-8",
            ),
        ],
    )


@contextmanager
def pipeline_logging(name: str) -> Iterator[None]:
    """Log START / SUCCESS / FAILURE with elapsed time for a pipeline."""
    logger = logging.getLogger(f"instagram_agent.pipelines.{name}")
    started = time.perf_counter()
    logger.info("START %s", name)
    try:
        yield
    except Exception:
        elapsed = time.perf_counter() - started
        logger.exception("FAILURE %s (%.2fs)", name, elapsed)
        raise
    else:
        elapsed = time.perf_counter() - started
        logger.info("SUCCESS %s (%.2fs)", name, elapsed)


def default_csv_path(stem: str) -> Path:
    settings = get_settings()
    settings.ensure_output_dirs()
    return settings.csv_dir / f"{stem}.csv"


def default_report_path(stem: str) -> Path:
    settings = get_settings()
    settings.ensure_output_dirs()
    return settings.reports_dir / f"{stem}.md"


def default_json_path(stem: str) -> Path:
    settings = get_settings()
    settings.ensure_output_dirs()
    return settings.reports_dir / f"{stem}.json"
