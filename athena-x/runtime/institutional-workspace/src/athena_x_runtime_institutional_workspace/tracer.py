"""Request Tracer — records every agent invocation during an analysis request.

For each request, the tracer builds a TraceRecord containing:
  - request_id (UUID)
  - symbol, timeframe
  - start_time, end_time, total_duration_ms
  - events: ordered list of (agent_id, layer, start_ms, duration_ms, output_summary, confidence)
  - contributor_chain: which agents contributed to the final conclusion

The tracer is non-blocking: agent execution is unaffected. The tracer
wraps each call in a timing context manager and stores the result.
"""
from __future__ import annotations
import asyncio
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from athena_x_runtime_logger import get_logger

log = get_logger("institutional-workspace.tracer")


@dataclass
class TraceEvent:
    """One agent invocation within a trace."""
    agent_id: str
    layer: int | str
    category: str
    started_at_ms: float          # monotonic ms
    duration_ms: float
    success: bool
    output_summary: str           # short description of what the agent returned
    confidence: float | None
    error: str = ""

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "layer": self.layer,
            "category": self.category,
            "started_at_ms": round(self.started_at_ms, 3),
            "duration_ms": round(self.duration_ms, 3),
            "success": self.success,
            "output_summary": self.output_summary,
            "confidence": self.confidence,
            "error": self.error,
        }


@dataclass
class TraceRecord:
    """Full trace of one analysis request."""
    request_id: str
    symbol: str
    timeframe: str
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime | None = None
    total_duration_ms: float = 0.0
    events: list[TraceEvent] = field(default_factory=list)
    final_conclusion: str = ""
    contributor_chain: list[str] = field(default_factory=list)
    data_provider: str = ""
    success: bool = True
    error: str = ""

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "total_duration_ms": round(self.total_duration_ms, 3),
            "events": [e.to_dict() for e in self.events],
            "final_conclusion": self.final_conclusion,
            "contributor_chain": self.contributor_chain,
            "data_provider": self.data_provider,
            "success": self.success,
            "error": self.error,
        }


def _summarize_output(output: Any) -> str:
    """Produce a short human-readable summary of an agent's output."""
    if output is None:
        return "None"
    if hasattr(output, "indicator") and hasattr(output, "value"):
        # TAOutput
        v = output.value
        if isinstance(v, (int, float)):
            return f"{output.indicator}={v}"
        if isinstance(v, dict):
            keys = list(v.keys())[:4]
            return f"{output.indicator}={{{', '.join(keys)}}}"
        return f"{output.indicator}={v}"
    if isinstance(output, dict):
        keys = list(output.keys())[:5]
        return f"dict({', '.join(keys)})"
    return str(output)[:80]


def _extract_confidence(output: Any) -> float | None:
    if hasattr(output, "confidence") and hasattr(output.confidence, "score"):
        return output.confidence.score
    if isinstance(output, dict) and "confidence" in output:
        try:
            return float(output["confidence"])
        except Exception:
            return None
    return None


class RequestTracer:
    """Traces agent invocations during an analysis request.

    Usage:
        tracer = RequestTracer()
        record = tracer.start_request("SPY", "15m", data_provider="yahoo")
        async with tracer.trace_agent("ta.ema", layer=2, category="indicator"):
            result = await ema_adapter.execute(...)
        tracer.finish_request(record, final_conclusion="Bullish trend confirmed")
        record_dict = record.to_dict()
    """

    def __init__(self):
        self._current: TraceRecord | None = None

    def start_request(
        self,
        symbol: str,
        timeframe: str,
        data_provider: str = "",
    ) -> TraceRecord:
        """Start a new trace for an analysis request."""
        record = TraceRecord(
            request_id=str(uuid4()),
            symbol=symbol,
            timeframe=timeframe,
            data_provider=data_provider,
        )
        self._current = record
        log.info("trace_started", request_id=record.request_id,
                 symbol=symbol, timeframe=timeframe)
        return record

    @asynccontextmanager
    async def trace_agent(
        self,
        agent_id: str,
        layer: int | str,
        category: str,
    ):
        """Async context manager that times one agent invocation."""
        if self._current is None:
            # No active trace — yield without recording
            yield
            return

        record = self._current
        t0 = time.monotonic() * 1000.0
        success = True
        error = ""
        output = None
        try:
            yield
        except Exception as e:
            success = False
            error = f"{type(e).__name__}: {e}"
            raise
        finally:
            t1 = time.monotonic() * 1000.0
            duration_ms = t1 - t0
            event = TraceEvent(
                agent_id=agent_id,
                layer=layer,
                category=category,
                started_at_ms=t0,
                duration_ms=duration_ms,
                success=success,
                output_summary=_summarize_output(output) if output else "(no output captured)",
                confidence=_extract_confidence(output),
                error=error,
            )
            record.events.append(event)
            if success:
                record.contributor_chain.append(agent_id)

    def record_output(self, output: Any):
        """Call this inside the trace_agent context to capture the output."""
        # We re-write the last event's output_summary
        if self._current and self._current.events:
            last = self._current.events[-1]
            last.output_summary = _summarize_output(output)
            last.confidence = _extract_confidence(output)

    def finish_request(
        self,
        record: TraceRecord,
        final_conclusion: str = "",
        success: bool = True,
        error: str = "",
    ):
        """Finish a trace."""
        record.finished_at = datetime.now(timezone.utc)
        t0 = record.started_at.timestamp()
        t1 = record.finished_at.timestamp()
        record.total_duration_ms = (t1 - t0) * 1000.0
        record.final_conclusion = final_conclusion
        record.success = success
        record.error = error
        log.info("trace_finished",
                 request_id=record.request_id,
                 total_duration_ms=round(record.total_duration_ms, 2),
                 events=len(record.events),
                 contributors=len(record.contributor_chain))
        if self._current is record:
            self._current = None

    async def execute_with_trace(
        self,
        adapter,
        symbol: str,
        timeframe,
        repo,
        event_bus=None,
    ) -> Any:
        """Execute an adapter call with automatic tracing."""
        async with self.trace_agent(
            adapter.agent_id, adapter.layer, adapter.category
        ):
            output = await adapter.execute(symbol, timeframe, repo, event_bus)
            self.record_output(output)
            return output
