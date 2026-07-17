"""Snapshot Coordinator - Stage 6 req 5.

Prevents mixing stale and fresh data.

Problem:
  ES updated 09:30:01
  SPY updated 09:30:02
  VIX updated 09:29:57  <- stale

If TA AI runs immediately, it may combine inconsistent inputs.

Solution:
  The Snapshot Coordinator waits for required data within a configurable
  time window before publishing a synchronized snapshot.

  If a required feed is stale beyond threshold:
    - mark snapshot as "degraded" (configurable)
    - or block (configurable)
"""
from __future__ import annotations
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from threading import RLock
from typing import Any
from uuid import UUID, uuid4

from athena_x_runtime_event_envelope import EventEnvelope, create_event, EventPriority
from athena_x_runtime_logger import get_logger

log = get_logger("runtime.snapshot-coordinator")


class SnapshotStatus(str, Enum):
    SYNCED = "synced"          # All feeds within threshold
    DEGRADED = "degraded"      # Some feeds stale
    BLOCKED = "blocked"        # Required feeds missing
    TIMEOUT = "timeout"        # Wait window expired


@dataclass
class SnapshotConfig:
    """Configuration for the snapshot coordinator."""
    required_feeds: list[str] = field(default_factory=lambda: ["SPY", "ES", "VIX", "options", "news"])
    max_staleness_seconds: float = 5.0
    wait_timeout_seconds: float = 2.0
    on_stale: str = "degraded"  # "degraded" or "block"


@dataclass
class SnapshotResult:
    """Result of a snapshot coordination."""
    snapshot_id: UUID
    status: SnapshotStatus
    feeds: dict[str, datetime]  # feed -> last update time
    stale_feeds: list[str]
    missing_feeds: list[str]
    created_at: datetime
    correlation_id: UUID


class SnapshotCoordinator:
    """Waits for required feeds to be synchronized before publishing snapshot.

    Usage:
        coord = SnapshotCoordinator(config)
        coord.update_feed("SPY", datetime.now(timezone.utc))
        coord.update_feed("ES", datetime.now(timezone.utc))
        result = await coord.try_snapshot()
        if result.status == SnapshotStatus.SYNCED:
            # Publish market:snapshot event
    """

    def __init__(self, config: SnapshotConfig | None = None):
        self._config = config or SnapshotConfig()
        self._feed_times: dict[str, datetime] = {}
        self._lock = RLock()

    def update_feed(self, feed: str, timestamp: datetime) -> None:
        """Update the latest timestamp for a feed."""
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        with self._lock:
            self._feed_times[feed] = timestamp

    async def try_snapshot(self) -> SnapshotResult:
        """Attempt to create a synchronized snapshot.

        Returns immediately if all feeds are fresh.
        Otherwise waits up to wait_timeout_seconds.
        """
        # Wait for required feeds
        start = datetime.now(timezone.utc)
        deadline = start + timedelta(seconds=self._config.wait_timeout_seconds)

        while datetime.now(timezone.utc) < deadline:
            result = self._evaluate()
            if result.status == SnapshotStatus.SYNCED:
                return result
            if result.status == SnapshotStatus.BLOCKED and self._config.on_stale == "block":
                # Wait more for missing feeds
                await asyncio.sleep(0.01)
                continue
            if result.status == SnapshotStatus.DEGRADED and self._config.on_stale == "block":
                # Wait more for stale feeds
                await asyncio.sleep(0.01)
                continue
            # If on_stale == "degraded", return immediately
            return result

        # Timeout
        result = self._evaluate()
        if result.status != SnapshotStatus.SYNCED:
            result.status = SnapshotStatus.TIMEOUT
        return result

    def _evaluate(self) -> SnapshotResult:
        """Evaluate current feed state."""
        now = datetime.now(timezone.utc)
        feeds: dict[str, datetime] = {}
        stale: list[str] = []
        missing: list[str] = []

        with self._lock:
            for feed in self._config.required_feeds:
                ts = self._feed_times.get(feed)
                if ts is None:
                    missing.append(feed)
                else:
                    feeds[feed] = ts
                    age = (now - ts).total_seconds()
                    if age > self._config.max_staleness_seconds:
                        stale.append(feed)

        if missing:
            status = SnapshotStatus.BLOCKED
        elif stale:
            status = SnapshotStatus.DEGRADED if self._config.on_stale == "degraded" else SnapshotStatus.BLOCKED
        else:
            status = SnapshotStatus.SYNCED

        return SnapshotResult(
            snapshot_id=uuid4(),
            status=status,
            feeds=feeds,
            stale_feeds=stale,
            missing_feeds=missing,
            created_at=now,
            correlation_id=uuid4(),
        )

    def create_snapshot_event(self, result: SnapshotResult) -> EventEnvelope:
        """Create a market:snapshot event from a snapshot result."""
        return create_event(
            event_type="market:snapshot",
            source_agent="snapshot-coordinator",
            symbol="*",
            priority=EventPriority.HIGH,
            correlation_id=result.correlation_id,
            payload={
                "snapshot_id": str(result.snapshot_id),
                "status": result.status.value,
                "feeds": {k: v.isoformat() for k, v in result.feeds.items()},
                "stale_feeds": result.stale_feeds,
                "missing_feeds": result.missing_feeds,
                "created_at": result.created_at.isoformat(),
            },
        )

    def get_feed_status(self) -> dict[str, dict]:
        """Get current status of all feeds."""
        now = datetime.now(timezone.utc)
        with self._lock:
            result = {}
            for feed in self._config.required_feeds:
                ts = self._feed_times.get(feed)
                if ts is None:
                    result[feed] = {"status": "missing", "age_seconds": None}
                else:
                    age = (now - ts).total_seconds()
                    result[feed] = {
                        "status": "stale" if age > self._config.max_staleness_seconds else "fresh",
                        "age_seconds": age,
                        "last_update": ts.isoformat(),
                    }
            return result
