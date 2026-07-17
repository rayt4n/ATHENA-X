"""Validation pipeline orchestrator (Stage 3 req 1).

Runs records through 11 validators in order:
  1. Schema → 2. Timestamp → 3. Market Calendar → 4. Cross-Provider →
  5. Market Logic → 6. Completeness → 7. Duplicate → 8. Outlier →
  9. Confidence → 10. Quality Classification → 11. Market State

Blocking validators (1, 2, 3, 5, 7) halt the pipeline on REJECTED.
Non-blocking validators (4, 6, 8, 9, 10, 11) record warnings but continue.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from athena_x_runtime_validation_types import (
    ValidationResult, ValidationStatus, ValidationContext,
    QualityGrade, AuditEntry, VALIDATOR_VERSION,
    create_audit,
)
from athena_x_runtime_audit_trail import AuditTrail
from athena_x_runtime_logger import get_logger

from .base import BaseValidator

log = get_logger("validation.pipeline")


@dataclass
class PipelineResult:
    """Aggregated result of running all validators on a record."""
    record_id: str
    final_status: ValidationStatus
    confidence_score: float
    quality_grade: QualityGrade
    results: list[ValidationResult] = field(default_factory=list)
    validation_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    validator_version: str = VALIDATOR_VERSION

    @property
    def accepted(self) -> bool:
        """True if the record can enter the canonical database."""
        return self.final_status in (ValidationStatus.VERIFIED, ValidationStatus.WARNING)

    @property
    def quarantined(self) -> bool:
        return self.final_status in (ValidationStatus.QUARANTINED, ValidationStatus.REJECTED)

    def to_metadata(self) -> dict:
        """Convert to confidence metadata (Stage 3 req 4)."""
        return {
            "validation_status": self.final_status.value,
            "validation_time": self.validation_time.isoformat(),
            "validator_version": self.validator_version,
            "confidence_score": self.confidence_score,
            "quality_grade": self.quality_grade.value,
            "validation_reason": self.results[-1].reason.value if self.results else "unknown",
        }


class ValidationPipeline:
    """Orchestrates the 11-stage validation pipeline.

    Usage:
        pipeline = ValidationPipeline(
            validators=[schema, timestamp, calendar, ...],
            audit_trail=audit_trail,
        )
        result = await pipeline.validate(record, context)
        if result.accepted:
            # write to canonical DB
        else:
            # write to quarantine
    """

    def __init__(
        self,
        validators: list[BaseValidator],
        audit_trail: AuditTrail | None = None,
    ):
        self._validators = validators
        self._audit_trail = audit_trail
        self._record_count = 0
        self._accepted_count = 0
        self._rejected_count = 0
        self._quarantined_count = 0
        self._warning_count = 0

    async def validate(
        self,
        record: Any,
        context: ValidationContext,
    ) -> PipelineResult:
        """Run a record through all validators in order."""
        record_id = str(uuid4())
        self._record_count += 1

        results: list[ValidationResult] = []
        confidence = 1.0  # start at full confidence, deductions accumulate

        for validator in self._validators:
            if not validator.enabled:
                continue

            try:
                result = await validator.validate(record, context)
            except Exception as e:
                log.error("validator_exception",
                          validator=validator.name,
                          error=str(e))
                result = ValidationResult(
                    validatorName=validator.name,
                    status=ValidationStatus.WARNING,
                    reason="validator_error",
                    message=f"Validator raised: {e}",
                    confidenceDelta=-0.2,
                )

            results.append(result)
            confidence = max(0.0, min(1.0, confidence + result.confidence_delta))

            # Log to audit trail
            if self._audit_trail is not None:
                audit_entry = create_audit(
                    provider=context.provider,
                    validator=validator.name,
                    rule_triggered=result.reason.value,
                    original_value=record,
                    corrected_value=result.corrected_value,
                    decision=result.status,
                    symbol=context.symbol,
                    record_id=record_id,
                )
                self._audit_trail.log(audit_entry)

            # Blocking validators halt on REJECTED
            if validator.blocking and result.status == ValidationStatus.REJECTED:
                log.info("record_rejected",
                         validator=validator.name,
                         reason=result.reason.value,
                         symbol=context.symbol)
                self._rejected_count += 1
                return PipelineResult(
                    record_id=record_id,
                    final_status=ValidationStatus.REJECTED,
                    confidence_score=confidence,
                    quality_grade=QualityGrade.from_confidence(confidence),
                    results=results,
                )

            # Quarantined also halts (outlier, etc.)
            if result.status == ValidationStatus.QUARANTINED:
                self._quarantined_count += 1
                # Continue running remaining validators to collect all issues
                continue

        # Determine final status
        if not results:
            final_status = ValidationStatus.VERIFIED
        elif any(r.status == ValidationStatus.QUARANTINED for r in results):
            final_status = ValidationStatus.QUARANTINED
        elif any(r.status == ValidationStatus.WARNING for r in results):
            final_status = ValidationStatus.WARNING
            self._warning_count += 1
        else:
            final_status = ValidationStatus.VERIFIED
            self._accepted_count += 1

        grade = QualityGrade.from_confidence(confidence)

        return PipelineResult(
            record_id=record_id,
            final_status=final_status,
            confidence_score=confidence,
            quality_grade=grade,
            results=results,
        )

    def get_stats(self) -> dict:
        """Self-monitoring metrics (Stage 3 req 8)."""
        total = self._record_count
        return {
            "total_records": total,
            "accepted": self._accepted_count,
            "warnings": self._warning_count,
            "quarantined": self._quarantined_count,
            "rejected": self._rejected_count,
            "rejection_rate": (self._rejected_count / total) if total > 0 else 0.0,
            "quarantine_rate": (self._quarantined_count / total) if total > 0 else 0.0,
            "acceptance_rate": (self._accepted_count / total) if total > 0 else 0.0,
        }
