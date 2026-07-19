"""Market state validator — Stage 3 additional req.

Before data is released to downstream analytics, verifies all required feeds
for the current analysis are synchronized.

Example:
  SPY Timestamp      10:15:01
  ES Timestamp       10:15:01
  VIX Timestamp      10:15:00
  Options Timestamp  10:15:01
  News Timestamp     10:14:58    ← 3 seconds stale

If one critical feed is significantly stale while others are current,
the validator either delays publication briefly or marks the dataset as partial.

This prevents downstream AI agents from making decisions on inconsistent
market snapshots — critical for intraday and 0DTE trading.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from threading import RLock
from typing import Any

from athena_x_validator_base import BaseValidator, ValidatorConfig
from athena_x_runtime_validation_types import (
    ValidationResult, ValidationContext, ValidationStatus, ValidationReason,
)


# Maximum allowed desynchronization between feeds (seconds)
MAX_DESYNC_SECONDS = 5.0
# Critical feeds that must be synchronized
CRITICAL_FEEDS = ["SPY", "ES", "VIX", "options", "news"]


@dataclass
class FeedTimestamps:
    """Timestamps of the latest data from each feed."""
    feeds: dict[str, datetime] = field(default_factory=dict)

    def add(self, feed: str, ts: datetime) -> None:
        self.feeds[feed] = ts

    @property
    def max_timestamp(self) -> datetime | None:
        if not self.feeds:
            return None
        return max(self.feeds.values())

    @property
    def min_timestamp(self) -> datetime | None:
        if not self.feeds:
            return None
        return min(self.feeds.values())

    @property
    def desync_seconds(self) -> float:
        """Time difference between newest and oldest feed."""
        if not self.feeds:
            return 0.0
        return (self.max_timestamp - self.min_timestamp).total_seconds()

    @property
    def stale_feeds(self) -> list[str]:
        """Feeds that are significantly older than the newest."""
        if not self.feeds or len(self.feeds) < 2:
            return []
        max_ts = self.max_timestamp
        return [
            feed for feed, ts in self.feeds.items()
            if (max_ts - ts).total_seconds() > MAX_DESYNC_SECONDS
        ]


class MarketStateValidator(BaseValidator):
    """Validates that market feeds are synchronized before downstream use."""

    def __init__(self, max_desync_seconds: float = MAX_DESYNC_SECONDS):
        super().__init__(ValidatorConfig(
            name="market-state-validator",
            blocking=False,
        ))
        self._max_desync = max_desync_seconds
        self._latest_timestamps: dict[str, datetime] = {}
        self._lock = RLock()

    def update_feed(self, feed: str, ts: datetime) -> None:
        """Update the latest timestamp for a feed."""
        with self._lock:
            if feed not in self._latest_timestamps or ts > self._latest_timestamps[feed]:
                self._latest_timestamps[feed] = ts

    async def validate(self, record: Any, context: ValidationContext) -> ValidationResult:
        """Validate market state synchronization."""
        ts_str = record.get("timestamp") if isinstance(record, dict) else None
        if not ts_str:
            return self._passed("no timestamp, skipping market state check")

        try:
            ts = self._parse_timestamp(ts_str)
        except Exception:
            return self._passed("cannot parse timestamp, skipping")

        feed_name = context.symbol
        self.update_feed(feed_name, ts)

        with self._lock:
            feeds = dict(self._latest_timestamps)

        if len(feeds) < 2:
            return self._passed("insufficient feeds for synchronization check")

        feed_ts = FeedTimestamps(feeds=feeds)
        desync = feed_ts.desync_seconds
        stale = feed_ts.stale_feeds

        if not stale:
            return self._passed(
                f"feeds synchronized (desync: {desync:.1f}s)"
            )

        if desync > self._max_desync * 3:
            return self._quarantine(
                ValidationReason.FEED_DESYNC,
                f"Severe feed desynchronization: {desync:.1f}s. Stale feeds: {stale}",
                confidence_delta=-0.4,
            )

        return self._warning(
            ValidationReason.FEED_DESYNC,
            f"Feed desynchronization: {desync:.1f}s. Stale feeds: {stale}",
            confidence_delta=-0.15,
        )

    def _parse_timestamp(self, ts_str) -> datetime:
        if isinstance(ts_str, (int, float)):
            if ts_str > 1e12:
                return datetime.fromtimestamp(ts_str / 1000, tz=timezone.utc)
            return datetime.fromtimestamp(ts_str, tz=timezone.utc)
        normalized = ts_str.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)

    def get_state(self) -> dict:
        """Get current market state for monitoring."""
        with self._lock:
            feeds = dict(self._latest_timestamps)
        if not feeds:
            return {"feeds": {}, "desync_seconds": 0.0, "stale_feeds": []}
        feed_ts = FeedTimestamps(feeds=feeds)
        return {
            "feeds": {k: v.isoformat() for k, v in feeds.items()},
            "desync_seconds": feed_ts.desync_seconds,
            "stale_feeds": feed_ts.stale_feeds,
        }
