"""Base standardizer — Stage 4 req.

A standardizer transforms a validated record into a canonical record.
The 8-stage pipeline runs:
  1. Symbol standardization
  2. Timezone standardization
  3. Market calendar standardization
  4. Unit standardization
  5. Field mapping
  6. Precision standardization
  7. Asset classification
  8. Canonical schema builder

Standardizers are pure functions — deterministic, replayable.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass
class StandardizationContext:
    """Context for standardization (deterministic)."""
    provider: str
    provider_version: str = "1.0.0"
    # Original provider timestamp (never lost — Stage 4 req 4)
    original_timestamp: datetime | None = None
    original_symbol: str | None = None
    # Validation metadata (from Stage 3)
    validation_id: str | None = None
    validation_status: str = "verified"
    confidence_score: float = 1.0
    quality_grade: str = "A"
    # Raw payload ID (for provenance)
    raw_payload_id: str | None = None


class BaseStandardizer(ABC):
    """Abstract base class for all 8 standardization steps."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def standardize(self, record: dict, context: StandardizationContext) -> dict:
        """Transform a record. MUST be deterministic.

        Args:
            record: the validated record (dict)
            context: standardization context

        Returns:
            The transformed record (modified dict).
        """
        ...


def generate_transformation_id() -> str:
    """Generate a unique transformation ID for provenance."""
    return str(uuid4())
