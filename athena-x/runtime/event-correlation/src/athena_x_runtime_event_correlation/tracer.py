"""Correlation tracer - Stage 6 req 4.

Every event generated from the same market snapshot shares a correlation ID.

Correlation: 2026-07-18T09:30:01.250Z
  |
  +-> ES Tick
  +-> SPY Update
  +-> Option Chain
  +-> Technical Analysis
  +-> Forecast
  +-> Dashboard

This allows tracing an entire processing pipeline from one market update.
"""
from __future__ import annotations
from collections import defaultdict
from datetime import datetime, timezone
from threading import RLock
from typing import Any
from uuid import UUID

from athena_x_runtime_event_envelope import EventEnvelope, create_event, EventPriority
from athena_x_runtime_logger import get_logger

log = get_logger("runtime.event-correlation")


class TraceEntry:
    """A single entry in a correlation trace."""
    def __init__(
        self,
        event_id: UUID,
        event_type: str,
        source_agent: str,
        timestamp: datetime,
        symbol: str | None = None,
    ):
        self.event_id = event_id
        self.event_type = event_type
        self.source_agent = source_agent
        self.timestamp = timestamp
        self.symbol = symbol

    def __repr__(self) -> str:
        return f"TraceEntry({self.event_type} from {self.source_agent} at {self.timestamp})"


class CorrelationTracer:
    """Tracks events by correlation ID for end-to-end tracing.

    Usage:
        tracer = CorrelationTracer()
        tracer.track(event)  # call for every event published
        trace = tracer.get_trace(correlation_id)
        # trace is a list of TraceEntry showing the full pipeline
    """

    def __init__(self, max_traces: int = 10000):
        self._traces: dict[UUID, list[TraceEntry]] = defaultdict(list)
        self._lock = RLock()
        self._max_traces = max_traces

    def track(self, event: EventEnvelope) -> None:
        """Track an event for its correlation ID."""
        with self._lock:
            entry = TraceEntry(
                event_id=event.event_id,
                event_type=event.event_type,
                source_agent=event.source_agent,
                timestamp=event.timestamp,
                symbol=event.symbol,
            )
            self._traces[event.correlation_id].append(entry)

            # Evict old traces if over limit
            if len(self._traces) > self._max_traces:
                oldest = min(self._traces.keys())
                del self._traces[oldest]

    def get_trace(self, correlation_id: UUID) -> list[TraceEntry]:
        """Get the full trace for a correlation ID."""
        with self._lock:
            return list(self._traces.get(correlation_id, []))

    def get_trace_summary(self, correlation_id: UUID) -> dict:
        """Get a summary of the trace."""
        trace = self.get_trace(correlation_id)
        if not trace:
            return {}

        return {
            "correlation_id": str(correlation_id),
            "event_count": len(trace),
            "event_types": [e.event_type for e in trace],
            "agents_involved": list(set(e.source_agent for e in trace)),
            "symbols": list(set(e.symbol for e in trace if e.symbol)),
            "start_time": trace[0].timestamp.isoformat(),
            "end_time": trace[-1].timestamp.isoformat(),
            "duration_ms": (trace[-1].timestamp - trace[0].timestamp).total_seconds() * 1000,
        }

    def create_child_event(
        self,
        parent: EventEnvelope,
        event_type: str,
        source_agent: str,
        payload: Any = None,
        priority: EventPriority | None = None,
    ) -> EventEnvelope:
        """Create a child event that shares the parent's correlation ID."""
        return create_event(
            event_type=event_type,
            source_agent=source_agent,
            payload=payload,
            symbol=parent.symbol,
            priority=priority or parent.priority,
            correlation_id=parent.correlation_id,
        )

    def active_correlations(self) -> int:
        """Number of active correlation IDs being tracked."""
        with self._lock:
            return len(self._traces)

    def clear(self) -> None:
        with self._lock:
            self._traces.clear()
