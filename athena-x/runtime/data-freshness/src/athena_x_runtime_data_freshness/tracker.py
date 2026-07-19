"""Data freshness tracker — Stage 2 req 1.9.

Every stream publishes:
  - expected_update_frequency (e.g., 1s for ES, 15s for VIX)
  - actual_update_frequency (rolling avg)
  - last_received_timestamp
  - status: fresh / delayed / stale

Status definitions:
  - fresh:  last_received within 1.5× expected frequency
  - delayed: last_received within 3× expected frequency
  - stale:  last_received > 3× expected frequency

This prevents the AI from making decisions on outdated information.
"""
from __future__ import annotations
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from threading import Lock
from typing import Deque

from athena_x_runtime_logger import get_logger

log = get_logger("runtime.data-freshness")


class FreshnessStatus(str, Enum):
    FRESH = "fresh"
    DELAYED = "delayed"
    STALE = "stale"
    NO_DATA = "no-data"


@dataclass
class StreamStats:
    """Statistics for a single data stream (symbol + provider)."""
    stream_id: str  # "{provider}:{symbol}"
    expected_frequency_s: float  # expected update interval in seconds
    last_received: datetime | None = None
    actual_frequency_s: float | None = None  # rolling avg
    total_received: int = 0
    status: FreshnessStatus = FreshnessStatus.NO_DATA
    recent_intervals: Deque[float] = field(default_factory=lambda: deque(maxlen=100))


class FreshnessTracker:
    """Tracks freshness of all data streams.

    Usage:
        tracker = FreshnessTracker()
        tracker.register_stream("yahoo:NVDA", expected_frequency_s=1.0)
        tracker.record_receipt("yahoo:NVDA")
        status = tracker.get_status("yahoo:NVDA")
        # status.status == FreshnessStatus.FRESH
    """

    def __init__(self):
        self._streams: dict[str, StreamStats] = {}
        self._lock = Lock()

    def register_stream(self, stream_id: str, expected_frequency_s: float) -> None:
        """Register a new stream with its expected update frequency."""
        with self._lock:
            if stream_id not in self._streams:
                self._streams[stream_id] = StreamStats(
                    stream_id=stream_id,
                    expected_frequency_s=expected_frequency_s,
                )
                log.info("stream_registered",
                         stream_id=stream_id,
                         expected_frequency_s=expected_frequency_s)

    def record_receipt(self, stream_id: str, timestamp: datetime | None = None) -> FreshnessStatus:
        """Record that a stream received an update.

        Args:
            stream_id: "{provider}:{symbol}" identifier
            timestamp: optional — defaults to now (UTC)

        Returns:
            The new FreshnessStatus for this stream.
        """
        ts = timestamp or datetime.now(timezone.utc)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)

        with self._lock:
            stream = self._streams.get(stream_id)
            if stream is None:
                log.warning("unregistered_stream", stream_id=stream_id)
                return FreshnessStatus.NO_DATA

            # Compute interval since last receipt
            if stream.last_received is not None:
                interval = (ts - stream.last_received).total_seconds()
                stream.recent_intervals.append(interval)
                # Rolling average
                if stream.recent_intervals:
                    stream.actual_frequency_s = sum(stream.recent_intervals) / len(stream.recent_intervals)

            stream.last_received = ts
            stream.total_received += 1
            stream.status = self._compute_status(stream, ts)
            return stream.status

    def get_status(self, stream_id: str) -> FreshnessStatus:
        """Get the current status of a stream (recomputes staleness)."""
        with self._lock:
            stream = self._streams.get(stream_id)
            if stream is None:
                return FreshnessStatus.NO_DATA
            stream.status = self._compute_status(stream, datetime.now(timezone.utc))
            return stream.status

    def get_stats(self, stream_id: str) -> StreamStats | None:
        """Get full stats for a stream."""
        with self._lock:
            stream = self._streams.get(stream_id)
            if stream is None:
                return None
            # Recompute status before returning
            stream.status = self._compute_status(stream, datetime.now(timezone.utc))
            return stream

    def list_all_streams(self) -> list[StreamStats]:
        """List all registered streams with current status."""
        with self._lock:
            now = datetime.now(timezone.utc)
            for stream in self._streams.values():
                stream.status = self._compute_status(stream, now)
            return list(self._streams.values())

    def list_stale_streams(self) -> list[StreamStats]:
        """Return only stale streams (for alerting)."""
        return [s for s in self.list_all_streams() if s.status == FreshnessStatus.STALE]

    def _compute_status(self, stream: StreamStats, now: datetime) -> FreshnessStatus:
        """Compute the freshness status based on time since last receipt."""
        if stream.last_received is None:
            return FreshnessStatus.NO_DATA

        age_s = (now - stream.last_received).total_seconds()
        expected = stream.expected_frequency_s

        if age_s <= 1.5 * expected:
            return FreshnessStatus.FRESH
        if age_s <= 3.0 * expected:
            return FreshnessStatus.DELAYED
        return FreshnessStatus.STALE
