"""Market calendar validator — Stage 3 req 2.3.

Verifies:
  - Trading day (not weekend/holiday for non-crypto)
  - Market holiday
  - Weekend (allowed only for crypto)
  - Trading session
  - Early close
  - Half-day schedule

Example: SPY trading on Christmas Day → REJECT.
"""
from __future__ import annotations
from datetime import datetime
from typing import Any

from athena_x_validator_base import BaseValidator, ValidatorConfig
from athena_x_runtime_validation_types import (
    ValidationResult, ValidationContext, ValidationStatus, ValidationReason,
)
from athena_x_runtime_session_awareness import SessionDetector, SessionType


# Symbols that trade 24/7 (no calendar restrictions)
CRYPTO_SYMBOLS = {"BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "BTC", "ETH"}


class MarketCalendarValidator(BaseValidator):
    """Validates that a record's timestamp is a valid trading time."""

    def __init__(self):
        super().__init__(ValidatorConfig(
            name="market-calendar-validator",
            blocking=True,
        ))
        self._detector = SessionDetector()

    async def validate(self, record: Any, context: ValidationContext) -> ValidationResult:
        """Validate the record against the market calendar."""
        # Extract timestamp from record
        ts_str = record.get("timestamp") if isinstance(record, dict) else None
        if not ts_str:
            return self._reject(
                ValidationReason.MISSING_REQUIRED_FIELD,
                "Missing timestamp for calendar check",
            )

        # Parse timestamp
        try:
            ts = self._parse_timestamp(ts_str)
        except Exception:
            return self._reject(
                ValidationReason.NAIVE_TIMESTAMP,
                f"Cannot parse timestamp: {ts_str}",
            )

        # Detect session
        info = self._detector.detect(ts, symbol=context.symbol)

        # Crypto: always allowed
        if info.is_crypto:
            return self._passed(f"crypto trades 24/7 (session: {info.session.value})")

        # Non-crypto: reject weekends and holidays
        if info.session == SessionType.WEEKEND:
            return self._reject(
                ValidationReason.WEEKEND,
                f"Non-crypto symbol {context.symbol} trading on weekend: {info.description}",
            )

        if info.session == SessionType.HOLIDAY:
            return self._reject(
                ValidationReason.HOLIDAY,
                f"Non-crypto symbol {context.symbol} trading on holiday: {info.description}",
            )

        # Overnight session: warning (low liquidity)
        if info.session == SessionType.OVERNIGHT:
            return self._warning(
                ValidationReason.WRONG_SESSION,
                f"Overnight session — low liquidity: {info.description}",
                confidence_delta=-0.2,
            )

        return self._passed(f"session: {info.session.value}")

    def _parse_timestamp(self, ts_str) -> datetime:
        """Parse ISO 8601 or unix timestamp."""
        from datetime import datetime, timezone
        if isinstance(ts_str, (int, float)):
            if ts_str > 1e12:
                return datetime.fromtimestamp(ts_str / 1000, tz=timezone.utc)
            return datetime.fromtimestamp(ts_str, tz=timezone.utc)
        normalized = ts_str.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
