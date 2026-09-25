"""Structured logging configuration with a stdlib fallback for minimal environments."""

from __future__ import annotations

import logging
import sys
from typing import Any

from utils.config import settings

try:  # Optional locally; requirements.txt installs structlog in normal environments.
    import structlog
except ImportError:  # pragma: no cover - exercised only in minimal CI/runtime images
    structlog = None  # type: ignore[assignment]


class _FallbackLogger:
    def __init__(self, logger: logging.Logger):
        self._logger = logger

    def info(self, event: str, **kwargs: Any) -> None:
        self._logger.info("%s %s", event, kwargs)

    def warning(self, event: str, **kwargs: Any) -> None:
        self._logger.warning("%s %s", event, kwargs)

    def error(self, event: str, **kwargs: Any) -> None:
        self._logger.error("%s %s", event, kwargs)

    def debug(self, event: str, **kwargs: Any) -> None:
        self._logger.debug("%s %s", event, kwargs)


def configure_logging() -> None:
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
    )
    if structlog is not None:
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(
                getattr(logging, settings.log_level.upper(), logging.INFO)
            ),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )


def get_logger(name: str):
    if structlog is not None:
        return structlog.get_logger(name)
    return _FallbackLogger(logging.getLogger(name))


configure_logging()
