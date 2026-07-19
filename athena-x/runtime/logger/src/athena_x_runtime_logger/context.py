"""Log context with correlation IDs (thread-safe via contextvars)."""
from __future__ import annotations
from contextvars import ContextVar
from contextlib import contextmanager
from dataclasses import dataclass, field
from uuid import uuid4
from typing import Iterator

_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")
_causation_id: ContextVar[str] = ContextVar("causation_id", default="")
_agent_id: ContextVar[str] = ContextVar("agent_id", default="")
_request_id: ContextVar[str] = ContextVar("request_id", default="")


@dataclass(frozen=True)
class LogContext:
    """Snapshot of current log context. Use as `with log_context(...):`."""
    correlation_id: str = ""
    causation_id: str = ""
    agent_id: str = ""
    request_id: str = ""

    def to_dict(self) -> dict:
        return {
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "agent_id": self.agent_id,
            "request_id": self.request_id,
        }


def new_correlation_id() -> str:
    """Generate a new correlation ID."""
    return str(uuid4())


def set_correlation_id(cid: str) -> None:
    _correlation_id.set(cid)


def get_correlation_id() -> str:
    return _correlation_id.get()


def set_agent_id(agent_id: str) -> None:
    _agent_id.set(agent_id)


def get_agent_id() -> str:
    return _agent_id.get()


@contextmanager
def log_context(
    *,
    correlation_id: str | None = None,
    causation_id: str | None = None,
    agent_id: str | None = None,
    request_id: str | None = None,
) -> Iterator[LogContext]:
    """Bind log context vars for the duration of the block.

    Usage:
        with log_context(agent_id="ta.rsi"):
            logger.info("computing RSI")  # includes agent_id=ta.rsi
    """
    cid = correlation_id or new_correlation_id()
    reset_tokens = []
    reset_tokens.append(_correlation_id.set(cid))
    if causation_id is not None:
        reset_tokens.append(_causation_id.set(causation_id))
    if agent_id is not None:
        reset_tokens.append(_agent_id.set(agent_id))
    if request_id is not None:
        reset_tokens.append(_request_id.set(request_id))

    try:
        yield LogContext(
            correlation_id=cid,
            causation_id=_causation_id.get(),
            agent_id=_agent_id.get(),
            request_id=_request_id.get(),
        )
    finally:
        for token in reversed(reset_tokens):
            token.var.reset(token)
