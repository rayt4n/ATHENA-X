"""Stage 3 validation types.

Every record passes through 11 validators. Each produces a ValidationResult.
The pipeline aggregates results into a final decision:
  - Verified   → write to canonical DB
  - Warning    → write to canonical DB + flag
  - Quarantined→ write to quarantine DB
  - Rejected   → write to quarantine DB

Nothing is silently fixed. Every decision is logged in the audit trail.
"""
from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field, field_validator


VALIDATOR_VERSION = "1.0.0"


class ValidationStatus(str, Enum):
    """4 possible outcomes (never just pass/fail)."""
    VERIFIED = "verified"
    WARNING = "warning"
    QUARANTINED = "quarantined"
    REJECTED = "rejected"


class QualityGrade(str, Enum):
    """6 quality grades (Stage 3 req 5)."""
    A_PLUS = "A+"   # Institutional (≥ 0.99)
    A = "A"          # Verified (≥ 0.95)
    B = "B"          # Acceptable (≥ 0.80)
    C = "C"          # Low Confidence (≥ 0.60)
    D = "D"          # Quarantine (≥ 0.30)
    F = "F"          # Reject (< 0.30)

    @classmethod
    def from_confidence(cls, confidence: float) -> "QualityGrade":
        """Map a confidence score to a quality grade."""
        if confidence >= 0.99:
            return cls.A_PLUS
        if confidence >= 0.95:
            return cls.A
        if confidence >= 0.80:
            return cls.B
        if confidence >= 0.60:
            return cls.C
        if confidence >= 0.30:
            return cls.D
        return cls.F


class ValidationReason(str, Enum):
    """Specific reasons a validator might flag a record."""
    # Schema
    MISSING_REQUIRED_FIELD = "missing_required_field"
    INVALID_DATA_TYPE = "invalid_data_type"
    NULL_VALUE = "null_value"
    INVALID_PRECISION = "invalid_precision"
    INVALID_SYMBOL = "invalid_symbol"
    # Timestamp
    NAIVE_TIMESTAMP = "naive_timestamp"
    FUTURE_TIMESTAMP = "future_timestamp"
    STALE_TIMESTAMP = "stale_timestamp"
    CLOCK_DRIFT = "clock_drift"
    OUT_OF_ORDER = "out_of_order"
    DUPLICATE_TIMESTAMP = "duplicate_timestamp"
    # Calendar
    NON_TRADING_DAY = "non_trading_day"
    HOLIDAY = "holiday"
    WEEKEND = "weekend"
    WRONG_SESSION = "wrong_session"
    # Cross-provider
    CONSENSUS_DISAGREEMENT = "consensus_disagreement"
    SINGLE_SOURCE = "single_source"
    # Market logic
    HIGH_LT_LOW = "high_lt_low"
    CLOSE_GT_HIGH = "close_gt_high"
    NEGATIVE_VOLUME = "negative_volume"
    NEGATIVE_OI = "negative_oi"
    IV_TOO_HIGH = "iv_too_high"
    IMPOSSIBLE_GREEK = "impossible_greek"
    # Completeness
    MISSING_BAR = "missing_bar"
    MISSING_STRIKE = "missing_strike"
    MISSING_EXPIRY = "missing_expiry"
    MISSING_GREEK = "missing_greek"
    # Duplicate
    DUPLICATE_PAYLOAD = "duplicate_payload"
    # Outlier
    STATISTICAL_OUTLIER = "statistical_outlier"
    CIRCUIT_BREAKER = "circuit_breaker"
    # Freshness
    STALE_DATA = "stale_data"
    # Market state
    FEED_DESYNC = "feed_desynchronization"
    # General
    PASSED = "passed"
    UNKNOWN = "unknown"


class ValidationContext(BaseModel):
    """Context passed to each validator. Deterministic — no time-dependent logic."""
    model_config = ConfigDict(populate_by_name=True)

    validator_version: str = Field(default=VALIDATOR_VERSION, alias="validatorVersion")
    pipeline_started_at: datetime = Field(alias="pipelineStartedAt")
    provider: str
    symbol: str
    asset_class: str
    # Optional: peers (for cross-provider validation)
    peer_values: dict[str, Any] = Field(default_factory=dict, alias="peerValues")
    # Optional: historical context (for outlier detection)
    recent_values: list[float] = Field(default_factory=list, alias="recentValues")
    # Optional: expected fields (for completeness)
    expected_fields: list[str] = Field(default_factory=list, alias="expectedFields")


class ValidationResult(BaseModel):
    """Result of a single validator's check on a record."""
    model_config = ConfigDict(populate_by_name=True)

    validator_name: str = Field(alias="validatorName")
    status: ValidationStatus
    reason: ValidationReason = Field(default=ValidationReason.PASSED)
    confidence_delta: float = Field(
        default=0.0, ge=-1.0, le=1.0, alias="confidenceDelta",
        description="Adjustment to the record's confidence score (-1..1)",
    )
    message: str = Field(default="")
    corrected_value: Any | None = Field(default=None, alias="correctedValue")
    metadata: dict[str, Any] = Field(default_factory=dict)


class AuditEntry(BaseModel):
    """A single audit trail entry (Stage 3 req 7).

    Every validation decision is logged. Nothing is silently fixed.
    """
    model_config = ConfigDict(populate_by_name=True)

    audit_id: UUID = Field(default_factory=uuid4, alias="auditId")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provider: str
    validator: str
    rule_triggered: str
    original_value: Any
    corrected_value: Any | None = None
    decision: ValidationStatus
    validator_version: str = Field(default=VALIDATOR_VERSION, alias="validatorVersion")
    symbol: str
    record_id: str | None = None


class QuarantineRecord(BaseModel):
    """A quarantined record (Stage 3 req 10).

    Never delete rejected data. Store with full context for debugging/auditing.
    """
    model_config = ConfigDict(populate_by_name=True)

    quarantine_id: UUID = Field(default_factory=uuid4, alias="quarantineId")
    quarantined_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc),
                                      alias="quarantinedAt")
    provider: str
    symbol: str
    raw_payload: Any
    reason: ValidationReason
    validator: str
    error_code: str
    original_timestamp: datetime | None = None
    audit_id: UUID | None = Field(default=None, alias="auditId")
    quality_grade: QualityGrade = Field(default=QualityGrade.D, alias="qualityGrade")
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0, alias="confidenceScore")
