"""Structured logging for the Bazzar backend (structlog).

JSON-lines to a rotating file under ``<data_dir>/logs/app.log`` plus a
human-readable console stream. Call ``configure_logging()`` once at process
start (server, fetchers, CLI jobs), then ``get_logger(__name__)`` anywhere.
"""

from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path

import structlog

_configured = False


def configure_logging(log_dir: Path | None = None, level: str = "INFO") -> None:
    """Configure stdlib + structlog. Idempotent."""
    global _configured
    if _configured:
        return
    _configured = True

    from .settings import get_settings

    settings = get_settings()
    log_dir = log_dir or settings.log_dir
    log_dir.mkdir(parents=True, exist_ok=True)

    numeric_level = getattr(logging, level.upper(), logging.INFO)

    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / "app.log", maxBytes=5_000_000, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(logging.Formatter("%(message)s"))

    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter("%(message)s"))

    root = logging.getLogger()
    root.setLevel(numeric_level)
    root.handlers.clear()
    root.addHandler(file_handler)
    root.addHandler(console)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(numeric_level),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger. Safe to call before configure_logging()."""
    if not _configured:
        configure_logging()
    return structlog.get_logger(name)
