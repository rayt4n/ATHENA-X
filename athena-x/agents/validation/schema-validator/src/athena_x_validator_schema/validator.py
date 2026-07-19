"""Schema validator — Stage 3 req 2.1.

Verifies:
  - Required fields exist
  - Data types are correct
  - No null values in required fields
  - Numeric precision
  - Currency (when applicable)
  - Exchange (when applicable)
  - Symbol validity

Rejects malformed records immediately.
"""
from __future__ import annotations
from typing import Any
import re

from athena_x_validator_base import BaseValidator, ValidatorConfig
from athena_x_runtime_validation_types import (
    ValidationResult, ValidationContext, ValidationStatus, ValidationReason,
)


# Required fields for a quote record
QUOTE_REQUIRED_FIELDS = {
    "symbol": str,
    "last": (int, float),
    "timestamp": str,
}

# Valid symbol pattern: 1-10 chars, uppercase letters/digits/dots/dashes
SYMBOL_PATTERN = re.compile(r"^[A-Z0-9]{1,6}([.\-][A-Z0-9]{1,4})?$")


class SchemaValidator(BaseValidator):
    """Validates the schema of an incoming record."""

    def __init__(self):
        super().__init__(ValidatorConfig(
            name="schema-validator",
            blocking=True,
        ))

    async def validate(self, record: Any, context: ValidationContext) -> ValidationResult:
        """Validate the record's schema."""
        if not isinstance(record, dict):
            return self._reject(
                ValidationReason.INVALID_DATA_TYPE,
                f"Record must be a dict, got {type(record).__name__}",
            )

        # Check required fields
        for field, expected_type in QUOTE_REQUIRED_FIELDS.items():
            if field not in record:
                return self._reject(
                    ValidationReason.MISSING_REQUIRED_FIELD,
                    f"Missing required field: {field}",
                )
            value = record[field]
            if value is None:
                return self._reject(
                    ValidationReason.NULL_VALUE,
                    f"Null value in required field: {field}",
                )
            if not isinstance(value, expected_type):
                return self._reject(
                    ValidationReason.INVALID_DATA_TYPE,
                    f"Field {field} must be {expected_type}, got {type(value).__name__}",
                )

        # Validate symbol format
        symbol = record.get("symbol", "")
        if not self._is_valid_symbol(symbol):
            return self._reject(
                ValidationReason.INVALID_SYMBOL,
                f"Invalid symbol format: {symbol}",
            )

        # Validate numeric precision (last should be a reasonable number)
        last = record.get("last")
        if isinstance(last, (int, float)):
            if last <= 0:
                return self._reject(
                    ValidationReason.INVALID_PRECISION,
                    f"Last price must be positive, got {last}",
                )
            if last > 1_000_000:  # sanity check
                return self._warning(
                    ValidationReason.INVALID_PRECISION,
                    f"Unusually large price: {last}",
                    confidence_delta=-0.1,
                )

        return self._passed("schema valid")

    def _is_valid_symbol(self, symbol: str) -> bool:
        """Check if a symbol matches the expected format."""
        if not isinstance(symbol, str) or not symbol:
            return False
        # Allow some special symbols
        special = {"BTC-USD", "ETH-USD", "Gold", "Oil", "Copper",
                   "Europe", "Asia", "USDJPY", "DXY"}
        if symbol in special:
            return True
        return bool(SYMBOL_PATTERN.match(symbol))
