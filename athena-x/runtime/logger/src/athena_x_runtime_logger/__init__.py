"""ATHENA-X structured logger."""
from .logger import get_logger, configure_logging
from .context import (
    LogContext,
    log_context,
    new_correlation_id,
    set_correlation_id,
    get_correlation_id,
    set_agent_id,
    get_agent_id,
)

__all__ = [
    "get_logger",
    "configure_logging",
    "set_correlation_id",
    "get_correlation_id",
    "set_agent_id",
    "get_agent_id",
    "new_correlation_id",
    "LogContext",
    "log_context",
]
__version__ = "0.1.0"
