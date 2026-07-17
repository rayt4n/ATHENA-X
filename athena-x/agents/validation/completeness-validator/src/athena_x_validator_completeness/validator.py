"""Completeness validator — Stage 3 req 2.6.

Ensures:
  - No missing bars
  - No missing option strikes
  - No missing expirations
  - No missing Greeks
  - No missing timestamps

Detects gaps before storage.

For Stage 3, this validator checks that required fields per record type
are present and non-null. Bar sequence gap detection is a stateful check
that will be added in Stage 6 (Event Bus) when we have a sequence buffer.
"""
from __future__ import annotations
from typing import Any

from athena_x_validator_base import BaseValidator, ValidatorConfig
from athena_x_runtime_validation_types import (
    ValidationResult, ValidationContext, ValidationStatus, ValidationReason,
)


# Required fields by record type
EXPECTED_QUOTE_FIELDS = ["symbol", "last", "timestamp"]
EXPECTED_BAR_FIELDS = ["timestamp", "open", "high", "low", "close", "volume"]
EXPECTED_OPTION_FIELDS = ["symbol", "expiry", "strikes"]
EXPECTED_GREEK_FIELDS = ["delta", "gamma", "theta", "vega"]


class CompletenessValidator(BaseValidator):
    """Validates that records have all required fields."""

    def __init__(self):
        super().__init__(ValidatorConfig(
            name="completeness-validator",
            blocking=False,  # warning, not rejection
        ))

    async def validate(self, record: Any, context: ValidationContext) -> ValidationResult:
        """Validate record completeness."""
        if not isinstance(record, dict):
            return self._passed("non-dict, skipping")

        # Determine record type from context + fields
        if context.asset_class == "option":
            return self._validate_option_record(record)
        elif "open" in record and "high" in record and "low" in record:
            return self._validate_bar_record(record)
        else:
            return self._validate_quote_record(record)

    def _validate_quote_record(self, record: dict) -> ValidationResult:
        """Validate a quote record."""
        missing = [f for f in EXPECTED_QUOTE_FIELDS if f not in record or record[f] is None]
        if missing:
            return self._warning(
                ValidationReason.MISSING_BAR,
                f"Missing quote fields: {missing}",
                confidence_delta=-0.1 * len(missing),
            )
        return self._passed("quote complete")

    def _validate_bar_record(self, record: dict) -> ValidationResult:
        """Validate an OHLCV bar record."""
        missing = [f for f in EXPECTED_BAR_FIELDS if f not in record or record[f] is None]
        if missing:
            return self._warning(
                ValidationReason.MISSING_BAR,
                f"Missing bar fields: {missing}",
                confidence_delta=-0.15 * len(missing),
            )
        return self._passed("bar complete")

    def _validate_option_record(self, record: dict) -> ValidationResult:
        """Validate an options record."""
        missing = [f for f in EXPECTED_OPTION_FIELDS if f not in record or record[f] is None]
        if missing:
            return self._warning(
                ValidationReason.MISSING_STRIKE,
                f"Missing option fields: {missing}",
                confidence_delta=-0.15 * len(missing),
            )

        # Check that strikes have required greeks
        strikes = record.get("strikes", [])
        if isinstance(strikes, list):
            missing_greeks = 0
            for s in strikes:
                if not isinstance(s, dict):
                    continue
                call = s.get("call", {})
                put = s.get("put", {})
                for greek in EXPECTED_GREEK_FIELDS:
                    if call.get(greek) is None or put.get(greek) is None:
                        missing_greeks += 1

            if missing_greeks > 0:
                return self._warning(
                    ValidationReason.MISSING_GREEK,
                    f"{missing_greeks} missing greek values across strikes",
                    confidence_delta=-0.05 * min(missing_greeks, 10),
                )

        return self._passed("option record complete")
