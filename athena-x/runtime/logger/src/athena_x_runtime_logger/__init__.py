"""Structured logger."""
from __future__ import annotations
import structlog


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger bound to the given name (usually agent_id)."""
    return structlog.get_logger(name)


__all__ = ["get_logger"]
