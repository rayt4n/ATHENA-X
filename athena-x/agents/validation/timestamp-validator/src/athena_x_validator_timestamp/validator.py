"""Timestamp validator — Stage 3 req 2.2.

Checks:
  - UTC format (timezone-aware)
  - Exchange timestamp vs arrival timestamp
  - Clock drift (max 5 seconds)
  - Duplicate timestamps (same provider + symbol + ts)
  - Out-of-order events (ts older than last seen)

Rejects impossible timestamps.

Deterministic: uses the record's timestamp, not now(). The pipeline_started_at
in context serves as the "arrival" reference.
"""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from typing import Any
from threading import Lock

from athena_x_validator_base import BaseValidator, ValidatorConfig
from athena_x_runtime_validation_types import (
    ValidationResult, ValidationContext, ValidationStatus, ValidationReason,
)


MAX_CLOCK_DRIFT_SECONDS = 5.0
MAX_FUTURE_SECONDS = 60.0  # allow up to 1 minute in the future (network delay)
MAX_STALE_SECONDS = 300.0  # 5 minutes


class TimestampValidator(BaseValidator):
    """Validates timestamps in a record."""

    def __init__(self):
        super().__init__(ValidatorConfig(
            name="timestamp-validator",
            blocking=True,
        ))
        self._last_timestamps: dict[str, datetime] = {}  # {provider:symbol: ts}
        self._seen_timestamps: dict[str, set[datetime]] = {}  # for duplicate detection
        self._lock = Lock()

    async def validate(self, record: Any, context: ValidationContext) -> ValidationResult:
        """Validate the record's timestamp."""
        ts_str = record.get("timestamp") if isinstance(record, dict) else None
        if not ts_str:
            return self._reject(
                ValidationReason.MISSING_REQUIRED_FIELD,
                "Missing timestamp field",
            )

        # Parse timestamp
        try:
            ts = self._parse_timestamp(ts_str)
        except (ValueError, TypeError) as e:
            return self._reject(
                ValidationReason.NAIVE_TIMESTAMP,
                f"Invalid timestamp format: {ts_str} ({e})",
            )

        if ts.tzinfo is None:
            return self._reject(
                ValidationReason.NAIVE_TIMESTAMP,
                f"Timestamp must be UTC-aware: {ts_str}",
            )

        ts_utc = ts.astimezone(timezone.utc)

        # Check future timestamp (allow small tolerance)
        pipeline_started = context.pipeline_started_at
        if ts_utc > pipeline_started + timedelta(seconds=MAX_FUTURE_SECONDS):
            return self._reject(
                ValidationReason.FUTURE_TIMESTAMP,
                f"Timestamp is too far in the future: {ts_utc.isoformat()}",
            )

        # Check staleness
        age = (pipeline_started - ts_utc).total_seconds()
        if age > MAX_STALE_SECONDS:
            return self._warning(
                ValidationReason.STALE_TIMESTAMP,
                f"Timestamp is {age:.1f}s old",
                confidence_delta=-0.3,
            )

        # Check clock drift (ts vs pipeline start)
        drift = abs((ts_utc - pipeline_started).total_seconds())
        if drift > MAX_CLOCK_DRIFT_SECONDS:
            return self._warning(
                ValidationReason.CLOCK_DRIFT,
                f"Clock drift: {drift:.1f}s",
                confidence_delta=-0.1,
            )

        # Check out-of-order (per provider:symbol)
        key = f"{context.provider}:{context.symbol}"
        with self._lock:
            last_ts = self._last_timestamps.get(key)
            if last_ts and ts_utc < last_ts:
                return self._reject(
                    ValidationReason.OUT_OF_ORDER,
                    f"Out-of-order: {ts_utc.isoformat()} < {last_ts.isoformat()}",
                )

            # Check duplicate timestamp
            seen_set = self._seen_timestamps.setdefault(key, set())
            if ts_utc in seen_set:
                return self._reject(
                    ValidationReason.DUPLICATE_TIMESTAMP,
                    f"Duplicate timestamp: {ts_utc.isoformat()}",
                )

            # Update state
            self._last_timestamps[key] = ts_utc
            seen_set.add(ts_utc)
            # Trim seen set to last 1000 entries
            if len(seen_set) > 1000:
                seen_set.clear()
                seen_set.add(ts_utc)

        return self._passed("timestamp valid")

    def _parse_timestamp(self, ts_str: str) -> datetime:
        """Parse a timestamp string (ISO 8601 or unix-millis)."""
        if isinstance(ts_str, (int, float)):
            # Unix timestamp
            if ts_str > 1e12:
                # milliseconds
                return datetime.fromtimestamp(ts_str / 1000, tz=timezone.utc)
            return datetime.fromtimestamp(ts_str, tz=timezone.utc)

        if isinstance(ts_str, str):
            # ISO 8601
            normalized = ts_str.replace("Z", "+00:00")
            return datetime.fromisoformat(normalized)

        raise ValueError(f"Cannot parse timestamp: {ts_str}")
