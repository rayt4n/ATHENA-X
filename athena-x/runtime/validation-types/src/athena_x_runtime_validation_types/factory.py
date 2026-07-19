"""Factory functions for creating validation results."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .types import (
    ValidationStatus, QualityGrade, ValidationReason, ValidationResult,
    AuditEntry, QuarantineRecord, VALIDATOR_VERSION,
)


def create_result(
    validator_name: str,
    status: ValidationStatus,
    reason: ValidationReason = ValidationReason.PASSED,
    confidence_delta: float = 0.0,
    message: str = "",
    corrected_value: Any | None = None,
    metadata: dict | None = None,
) -> ValidationResult:
    """Create a ValidationResult."""
    return ValidationResult(
        validatorName=validator_name,
        status=status,
        reason=reason,
        confidenceDelta=confidence_delta,
        message=message,
        correctedValue=corrected_value,
        metadata=metadata or {},
    )


def create_audit(
    *,
    provider: str,
    validator: str,
    rule_triggered: str,
    original_value: Any,
    corrected_value: Any | None,
    decision: ValidationStatus,
    symbol: str,
    record_id: str | None = None,
) -> AuditEntry:
    """Create an AuditEntry."""
    return AuditEntry(
        audit_id=uuid4(),
        timestamp=datetime.now(timezone.utc),
        provider=provider,
        validator=validator,
        rule_triggered=rule_triggered,
        original_value=original_value,
        corrected_value=corrected_value,
        decision=decision,
        validator_version=VALIDATOR_VERSION,
        symbol=symbol,
        record_id=record_id,
    )


def create_quarantine(
    *,
    provider: str,
    symbol: str,
    raw_payload: Any,
    reason: ValidationReason,
    validator: str,
    error_code: str,
    original_timestamp: datetime | None = None,
    confidence_score: float = 0.0,
) -> QuarantineRecord:
    """Create a QuarantineRecord."""
    return QuarantineRecord(
        quarantine_id=uuid4(),
        quarantined_at=datetime.now(timezone.utc),
        provider=provider,
        symbol=symbol,
        raw_payload=raw_payload,
        reason=reason,
        validator=validator,
        error_code=error_code,
        original_timestamp=original_timestamp,
        confidence_score=confidence_score,
    )
