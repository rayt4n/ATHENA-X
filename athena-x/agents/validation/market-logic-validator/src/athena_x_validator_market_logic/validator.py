"""Market logic validator — Stage 3 req 2.5.

Detects impossible values:
  - High < Low
  - Close > High
  - Close < Low
  - Open > High or Open < Low
  - Negative Volume
  - Negative Open Interest
  - IV > 1000% (10.0 in decimal)
  - Impossible Greeks (|delta| > 1.5, gamma < 0, etc.)

Rejects.
"""
from __future__ import annotations
from typing import Any

from athena_x_validator_base import BaseValidator, ValidatorConfig
from athena_x_runtime_validation_types import (
    ValidationResult, ValidationContext, ValidationStatus, ValidationReason,
)


MAX_IV = 10.0  # 1000% in decimal
MAX_DELTA = 1.5  # allow some numerical error
MIN_GAMMA = -0.001  # allow tiny numerical error


class MarketLogicValidator(BaseValidator):
    """Validates market-logic invariants in a record."""

    def __init__(self):
        super().__init__(ValidatorConfig(
            name="market-logic-validator",
            blocking=True,
        ))

    async def validate(self, record: Any, context: ValidationContext) -> ValidationResult:
        """Validate market logic invariants."""
        if not isinstance(record, dict):
            return self._passed("non-dict, skipping")

        # OHLC checks
        high = record.get("high")
        low = record.get("low")
        open_p = record.get("open")
        close = record.get("close")

        if high is not None and low is not None:
            if high < low:
                return self._reject(
                    ValidationReason.HIGH_LT_LOW,
                    f"High ({high}) < Low ({low})",
                )

        if close is not None and high is not None:
            if close > high * 1.001:  # small tolerance for rounding
                return self._reject(
                    ValidationReason.CLOSE_GT_HIGH,
                    f"Close ({close}) > High ({high})",
                )

        if close is not None and low is not None:
            if close < low * 0.999:
                return self._reject(
                    ValidationReason.HIGH_LT_LOW,
                    f"Close ({close}) < Low ({low})",
                )

        if open_p is not None and high is not None and low is not None:
            if open_p > high * 1.001 or open_p < low * 0.999:
                return self._warning(
                    ValidationReason.HIGH_LT_LOW,
                    f"Open ({open_p}) outside [Low ({low}), High ({high})]",
                    confidence_delta=-0.1,
                )

        # Volume checks
        volume = record.get("volume")
        if volume is not None and volume < 0:
            return self._reject(
                ValidationReason.NEGATIVE_VOLUME,
                f"Negative volume: {volume}",
            )

        # Open interest checks
        oi = record.get("open_interest")
        if oi is not None and oi < 0:
            return self._reject(
                ValidationReason.NEGATIVE_OI,
                f"Negative open interest: {oi}",
            )

        # IV checks
        iv = record.get("iv")
        if iv is not None and isinstance(iv, (int, float)):
            if iv > MAX_IV:
                return self._reject(
                    ValidationReason.IV_TOO_HIGH,
                    f"IV {iv} exceeds max {MAX_IV} (1000%)",
                )
            if iv < 0:
                return self._reject(
                    ValidationReason.IV_TOO_HIGH,
                    f"Negative IV: {iv}",
                )

        # Greeks checks (if present)
        delta = record.get("delta")
        if delta is not None and isinstance(delta, (int, float)):
            if abs(delta) > MAX_DELTA:
                return self._reject(
                    ValidationReason.IMPOSSIBLE_GREEK,
                    f"Delta {delta} exceeds |{MAX_DELTA}|",
                )

        gamma = record.get("gamma")
        if gamma is not None and isinstance(gamma, (int, float)):
            if gamma < MIN_GAMMA:
                return self._reject(
                    ValidationReason.IMPOSSIBLE_GREEK,
                    f"Gamma {gamma} < {MIN_GAMMA} (gamma must be >= 0)",
                )

        theta = record.get("theta")
        if theta is not None and isinstance(theta, (int, float)):
            # Theta can be negative (time decay), but extreme values are suspicious
            if abs(theta) > 1000:
                return self._warning(
                    ValidationReason.IMPOSSIBLE_GREEK,
                    f"Extreme theta: {theta}",
                    confidence_delta=-0.2,
                )

        return self._passed("market logic valid")
