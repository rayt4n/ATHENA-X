"""Tests for validation types."""
import pytest
from athena_x_runtime_validation_types import (
    ValidationStatus, QualityGrade, ValidationReason,
    ValidationResult, AuditEntry, QuarantineRecord,
    VALIDATOR_VERSION,
)


def test_four_validation_statuses():
    """4 outcomes: verified, warning, quarantined, rejected."""
    assert ValidationStatus.VERIFIED.value == "verified"
    assert ValidationStatus.WARNING.value == "warning"
    assert ValidationStatus.QUARANTINED.value == "quarantined"
    assert ValidationStatus.REJECTED.value == "rejected"


def test_six_quality_grades():
    """6 quality grades: A+, A, B, C, D, F."""
    assert QualityGrade.A_PLUS.value == "A+"
    assert QualityGrade.A.value == "A"
    assert QualityGrade.B.value == "B"
    assert QualityGrade.C.value == "C"
    assert QualityGrade.D.value == "D"
    assert QualityGrade.F.value == "F"


def test_quality_grade_from_confidence():
    """Map confidence to grade."""
    assert QualityGrade.from_confidence(0.999) == QualityGrade.A_PLUS
    assert QualityGrade.from_confidence(0.97) == QualityGrade.A
    assert QualityGrade.from_confidence(0.85) == QualityGrade.B
    assert QualityGrade.from_confidence(0.65) == QualityGrade.C
    assert QualityGrade.from_confidence(0.45) == QualityGrade.D
    assert QualityGrade.from_confidence(0.15) == QualityGrade.F


def test_validator_version_is_semver():
    """Version is semver for replay determinism."""
    parts = VALIDATOR_VERSION.split(".")
    assert len(parts) == 3
    for p in parts:
        assert p.isdigit()


def test_validation_result_factory():
    from athena_x_runtime_validation_types import create_result
    r = create_result(
        validator_name="schema-validator",
        status=ValidationStatus.REJECTED,
        reason=ValidationReason.MISSING_REQUIRED_FIELD,
        confidence_delta=-0.5,
        message="missing 'last' field",
    )
    assert r.validator_name == "schema-validator"
    assert r.status == ValidationStatus.REJECTED
    assert r.confidence_delta == -0.5


def test_audit_entry_has_all_fields():
    """Audit entries have all 8 required fields."""
    from athena_x_runtime_validation_types import create_audit
    entry = create_audit(
        provider="yahoo",
        validator="schema-validator",
        rule_triggered="missing_required_field",
        original_value={"symbol": "SPY"},  # missing 'last'
        corrected_value=None,
        decision=ValidationStatus.REJECTED,
        symbol="SPY",
    )
    assert entry.provider == "yahoo"
    assert entry.validator == "schema-validator"
    assert entry.rule_triggered == "missing_required_field"
    assert entry.decision == ValidationStatus.REJECTED
    assert entry.validator_version == VALIDATOR_VERSION


def test_quarantine_record_has_all_fields():
    """Quarantine records have full context for debugging."""
    from athena_x_runtime_validation_types import create_quarantine
    q = create_quarantine(
        provider="yahoo",
        symbol="SPY",
        raw_payload={"last": 742.0},  # outlier
        reason=ValidationReason.STATISTICAL_OUTLIER,
        validator="outlier-detector",
        error_code="OUTLIER_001",
        confidence_score=0.1,
    )
    assert q.provider == "yahoo"
    assert q.symbol == "SPY"
    assert q.reason == ValidationReason.STATISTICAL_OUTLIER
    assert q.error_code == "OUTLIER_001"
    assert q.confidence_score == 0.1
