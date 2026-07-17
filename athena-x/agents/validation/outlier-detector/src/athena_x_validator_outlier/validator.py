"""Outlier detector — Stage 3 req 2.8.

Uses robust statistical techniques:
  - Median Absolute Deviation (MAD)
  - Rolling Z-score
  - Percent deviation from recent median
  - Circuit breaker thresholds

Outliers are QUARANTINED rather than silently discarded.

Determinism: uses context.recent_values (provided by pipeline), not internal state.
"""
from __future__ import annotations
import statistics
from typing import Any

from athena_x_validator_base import BaseValidator, ValidatorConfig
from athena_x_runtime_validation_types import (
    ValidationResult, ValidationContext, ValidationStatus, ValidationReason,
)


# Default thresholds
MAD_THRESHOLD = 5.0  # 5 MADs from median = outlier
Z_SCORE_THRESHOLD = 4.0  # 4 standard deviations
PCT_DEVIATION_THRESHOLD = 0.05  # 5% deviation from recent median
CIRCUIT_BREAKER_PCT = 0.20  # 20% deviation = circuit breaker
MIN_SAMPLES_FOR_STATS = 5  # need at least 5 recent values


class OutlierDetector(BaseValidator):
    """Detects statistical outliers using MAD and Z-score."""

    def __init__(
        self,
        mad_threshold: float = MAD_THRESHOLD,
        z_score_threshold: float = Z_SCORE_THRESHOLD,
        pct_deviation_threshold: float = PCT_DEVIATION_THRESHOLD,
        circuit_breaker_pct: float = CIRCUIT_BREAKER_PCT,
    ):
        super().__init__(ValidatorConfig(
            name="outlier-detector",
            blocking=False,  # quarantine, not reject (so other validators can still run)
        ))
        self._mad_threshold = mad_threshold
        self._z_threshold = z_score_threshold
        self._pct_threshold = pct_deviation_threshold
        self._circuit_breaker_pct = circuit_breaker_pct

    async def validate(self, record: Any, context: ValidationContext) -> ValidationResult:
        """Check if the record's 'last' value is a statistical outlier."""
        if not isinstance(record, dict):
            return self._passed("non-dict, skipping")

        value = record.get("last")
        if value is None or not isinstance(value, (int, float)):
            return self._passed("no 'last' field to check")

        recent = context.recent_values
        if len(recent) < MIN_SAMPLES_FOR_STATS:
            return self._passed(
                f"insufficient samples for outlier detection ({len(recent)} < {MIN_SAMPLES_FOR_STATS})"
            )

        # Compute statistics
        median = statistics.median(recent)
        mad = statistics.median([abs(v - median) for v in recent])

        # Circuit breaker: extreme deviation
        if median > 0:
            pct_deviation = abs(value - median) / median
            if pct_deviation > self._circuit_breaker_pct:
                return self._quarantine(
                    ValidationReason.CIRCUIT_BREAKER,
                    f"Circuit breaker: {pct_deviation:.2%} deviation from median {median:.2f}",
                    confidence_delta=-0.7,
                )

        # MAD-based outlier detection (robust)
        if mad > 0:
            modified_z = 0.6745 * (value - median) / mad
            if abs(modified_z) > self._mad_threshold:
                return self._quarantine(
                    ValidationReason.STATISTICAL_OUTLIER,
                    f"MAD outlier: z={modified_z:.2f} (threshold={self._mad_threshold})",
                    confidence_delta=-0.5,
                )

        # Z-score (less robust but standard)
        try:
            mean = statistics.mean(recent)
            stdev = statistics.stdev(recent)
            if stdev > 0:
                z = (value - mean) / stdev
                if abs(z) > self._z_threshold:
                    return self._quarantine(
                        ValidationReason.STATISTICAL_OUTLIER,
                        f"Z-score outlier: z={z:.2f} (threshold={self._z_threshold})",
                        confidence_delta=-0.4,
                    )
        except statistics.StatisticsError:
            pass  # not enough samples for stdev

        # Percent deviation warning
        if median > 0:
            pct = abs(value - median) / median
            if pct > self._pct_threshold:
                return self._warning(
                    ValidationReason.STATISTICAL_OUTLIER,
                    f"Above pct deviation: {pct:.2%} from median {median:.2f}",
                    confidence_delta=-0.1,
                )

        return self._passed(f"value {value} within normal range")
