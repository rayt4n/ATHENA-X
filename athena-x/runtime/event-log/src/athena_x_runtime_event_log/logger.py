"""Event log - Stage 6 req 7.

Every event is written to the event log. Later you can replay any time range.

09:30 -> 09:31 -> 09:32 -> 09:33

Invaluable for debugging and backtesting.

- Event log is append-only
- Deterministic replay (same events -> same outcomes)
- Supports time-range queries
"""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any
from uuid import UUID

from athena_x_runtime_event_envelope import EventEnvelope
from athena_x_runtime_logger import get_logger

log = get_logger("runtime.event-log")


@dataclass
class EventLogEntry:
    """A single entry in the event log."""
    sequence: int  # monotonic sequence number
    event: EventEnvelope
    logged_at: datetime


@dataclass
class ReplayResult:
    """Result of a replay operation."""
    events: list[EventEnvelope] = field(default_factory=list)
    total_count: int = 0
    replay_time_ms: float = 0.0
    time_range: tuple[datetime, datetime] | None = None


class EventLog:
    """Append-only event log with replay support.

    Usage:
        event_log = EventLog()
        await event_log.append(event)

        # Replay a time range
        result = await event_log.replay(
            start=datetime(2026, 7, 18, 9, 30, tzinfo=timezone.utc),
            end=datetime(2026, 7, 18, 9, 31, tzinfo=timezone.utc),
        )
        for event in result.events:
            # Re-process event
            pass
    """

    def __init__(self, persist_path: str | Path | None = None):
        self._entries: list[EventLogEntry] = []
        self._sequence = 0
        self._lock = RLock()
        self._persist_path = Path(persist_path) if persist_path else None
        if self._persist_path:
            self._persist_path.parent.mkdir(parents=True, exist_ok=True)

    async def append(self, event: EventEnvelope) -> int:
        """Append an event to the log. Returns the sequence number."""
        with self._lock:
            self._sequence += 1
            entry = EventLogEntry(
                sequence=self._sequence,
                event=event,
                logged_at=datetime.now(timezone.utc),
            )
            self._entries.append(entry)

        if self._persist_path:
            self._persist_entry(entry)

        return entry.sequence

    def _persist_entry(self, entry: EventLogEntry) -> None:
        """Append entry to filesystem log (JSONL format)."""
        try:
            with open(self._persist_path, "a", encoding="utf-8") as f:
                record = {
                    "sequence": entry.sequence,
                    "event": entry.event.model_dump(),
                    "logged_at": entry.logged_at.isoformat(),
                }
                f.write(json.dumps(record, default=str) + "\n")
        except Exception as e:
            log.error("event_log_persist_failed", error=str(e))

    async def replay(
        self,
        start: datetime | None = None,
        end: datetime | None = None,
        event_type: str | None = None,
        source_agent: str | None = None,
        correlation_id: UUID | None = None,
        limit: int | None = None,
    ) -> ReplayResult:
        """Replay events from the log.

        Args:
            start: filter events after this time
            end: filter events before this time
            event_type: filter by event type
            source_agent: filter by source agent
            correlation_id: filter by correlation ID
            limit: max events to return

        Returns:
            ReplayResult with matching events.
        """
        from time import perf_counter
        t0 = perf_counter()

        with self._lock:
            entries = list(self._entries)

        events: list[EventEnvelope] = []
        for entry in entries:
            event = entry.event

            # Apply filters
            if start and event.timestamp < start:
                continue
            if end and event.timestamp > end:
                continue
            if event_type and event.event_type != event_type:
                continue
            if source_agent and event.source_agent != source_agent:
                continue
            if correlation_id and event.correlation_id != correlation_id:
                continue

            events.append(event)
            if limit and len(events) >= limit:
                break

        elapsed_ms = (perf_counter() - t0) * 1000
        time_range = None
        if events:
            time_range = (events[0].timestamp, events[-1].timestamp)

        return ReplayResult(
            events=events,
            total_count=len(events),
            replay_time_ms=elapsed_ms,
            time_range=time_range,
        )

    async def replay_by_correlation(self, correlation_id: UUID) -> list[EventEnvelope]:
        """Replay all events with a specific correlation ID (end-to-end trace)."""
        result = await self.replay(correlation_id=correlation_id)
        return result.events

    def count(self) -> int:
        with self._lock:
            return len(self._entries)

    def get_stats(self) -> dict:
        with self._lock:
            if not self._entries:
                return {"total_events": 0}
            return {
                "total_events": len(self._entries),
                "first_event": self._entries[0].event.timestamp.isoformat(),
                "last_event": self._entries[-1].event.timestamp.isoformat(),
                "sequence": self._sequence,
            }

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()
            self._sequence = 0
