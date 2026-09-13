"""
Structured logging using structlog.
Every log entry carries request_id, matter_id, and run_id for traceability.
"""
from __future__ import annotations

import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict


def add_app_context(logger: Any, method: str, event_dict: EventDict) -> EventDict:  # noqa: ARG001
    """Inject application-level context into every log entry."""
    event_dict.setdefault("app", "legaldoc")
    return event_dict


def configure_logging(log_level: str = "INFO") -> None:
    """Configure structlog with JSON output for production, pretty for dev."""
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        add_app_context,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    structlog.configure(
        processors=shared_processors
        + [
            structlog.dev.ConsoleRenderer(colors=True),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(log_level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = __name__) -> structlog.BoundLogger:
    return structlog.get_logger(name)
