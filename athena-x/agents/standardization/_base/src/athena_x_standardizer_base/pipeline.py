"""Standardization pipeline — runs all 8 steps in order (Stage 4 req 1)."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from athena_x_runtime_logger import get_logger

from .base import BaseStandardizer, StandardizationContext
from .steps import (
    SymbolStandardizer, TimezoneStandardizer, CalendarStandardizer,
    UnitStandardizer, FieldMapper, PrecisionStandardizer,
    AssetClassifier, CanonicalSchemaBuilder,
)

log = get_logger("standardization.pipeline")


@dataclass
class StandardizationResult:
    """Result of running the standardization pipeline."""
    canonical_record: dict
    transformation_id: str
    schema_version: str
    mapping_version: str
    steps_completed: list[str] = field(default_factory=list)
    success: bool = True
    errors: list[str] = field(default_factory=list)


class StandardizationPipeline:
    """Orchestrates the 8-stage standardization pipeline.

    Order:
      1. Symbol standardization
      2. Timezone standardization
      3. Market calendar standardization
      4. Unit standardization
      5. Field mapping
      6. Precision standardization
      7. Asset classification
      8. Canonical schema builder
    """

    def __init__(self, steps: list[BaseStandardizer] | None = None):
        if steps is None:
            # Default 8-step pipeline
            self._steps: list[BaseStandardizer] = [
                SymbolStandardizer(),           # 1
                TimezoneStandardizer(),         # 2
                CalendarStandardizer(),         # 3
                UnitStandardizer(),             # 4
                FieldMapper(),                  # 5
                PrecisionStandardizer(),        # 6
                AssetClassifier(),              # 7
                CanonicalSchemaBuilder(),       # 8
            ]
        else:
            self._steps = steps

        self._record_count = 0
        self._error_count = 0

    def standardize(self, record: dict, context: StandardizationContext) -> StandardizationResult:
        """Run a record through all 8 steps."""
        self._record_count += 1
        steps_completed: list[str] = []
        errors: list[str] = []
        current = dict(record)  # don't mutate input

        for step in self._steps:
            try:
                current = step.standardize(current, context)
                steps_completed.append(step.name)
            except Exception as e:
                errors.append(f"{step.name}: {e}")
                self._error_count += 1
                log.error("standardization_step_failed",
                          step=step.name, error=str(e))

        transformation_id = current.get("transformation_id", "")
        schema_version = current.get("schema_version", "")
        mapping_version = current.get("mapping_version", "")

        return StandardizationResult(
            canonical_record=current,
            transformation_id=transformation_id,
            schema_version=schema_version,
            mapping_version=mapping_version,
            steps_completed=steps_completed,
            success=len(errors) == 0,
            errors=errors,
        )

    def get_stats(self) -> dict:
        return {
            "total_records": self._record_count,
            "errors": self._error_count,
            "steps": [s.name for s in self._steps],
        }
