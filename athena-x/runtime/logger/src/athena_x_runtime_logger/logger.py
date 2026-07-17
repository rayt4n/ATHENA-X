"""Structured logger using structlog.

Outputs JSON to stdout with:
- timestamp (ISO 8601 UTC)
- level
- message
- correlation_id, causation_id, agent_id, request_id (from contextvars)
- any extra fields passed by the caller
"""
from __future__ import annotations
import sys
import logging
import structlog
from .context import (
    _correlation_id,
    _causation_id,
    _agent_id,
    _request_id,
)


_CONFIGURED = False


def configure_logging(debug: bool = False, json_output: bool = True) -> None:
    """Configure structlog globally. Call once at startup."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    log_level = logging.DEBUG if debug else logging.INFO

    # Configure stdlib logging (structlog routes through it)
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        stream=sys.stdout,
        force=True,
    )

    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        _inject_correlation_ids,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if json_output:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    _CONFIGURED = True


def _inject_correlation_ids(_, __, event_dict: dict) -> dict:
    """Inject correlation IDs into every log event."""
    cid = _correlation_id.get()
    causation = _causation_id.get()
    agent = _agent_id.get()
    request = _request_id.get()
    if cid:
        event_dict["correlation_id"] = cid
    if causation:
        event_dict["causation_id"] = causation
    if agent:
        event_dict["agent_id"] = agent
    if request:
        event_dict["request_id"] = request
    return event_dict


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger bound to the given name.

    Args:
        name: usually the agent_id or module name (e.g., "ta.rsi", "data-collection.collection")

    Returns:
        A structlog BoundLogger that emits JSON to stdout.
    """
    if not _CONFIGURED:
        configure_logging()
    return structlog.get_logger(name)
