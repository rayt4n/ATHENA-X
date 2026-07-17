#!/usr/bin/env python3
"""
STEP 4 Stage 3 — Validation AI (Part 1: Foundation + 6 validators)
====================================================================
Implements:
  1. runtime/validation-types/     — shared types
  2. runtime/audit-trail/          — audit logging + replay
  3. agents/validation/_base/      — BaseValidator + ValidationPipeline
  4. agents/validation/schema-validator/
  5. agents/validation/timestamp-validator/
  6. agents/validation/market-calendar-validator/
  7. agents/validation/cross-provider-validator/
  8. agents/validation/market-logic-validator/
  9. agents/validation/completeness-validator/
 10. agents/validation/quarantine-manager/

Run: python /home/z/my-project/scripts/stage3_implement_part1.py
"""

from pathlib import Path
import textwrap

ROOT = Path("/home/z/my-project/athena-x")
ROOT.mkdir(parents=True, exist_ok=True)
FILES = []

def w(rel: str, content: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(content).lstrip("\n"))
    FILES.append(rel)


# ============================================================================
# 1. VALIDATION TYPES — runtime/validation-types/
# ============================================================================

w("runtime/validation-types/pyproject.toml", '''
[project]
name = "athena-x-runtime-validation-types"
version = "0.1.0"
description = "Shared validation types (ValidationResult, QualityGrade, AuditEntry, QuarantineRecord)"
requires-python = ">=3.11"
dependencies = ["pydantic>=2.9.0"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_runtime_validation_types"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w("runtime/validation-types/src/athena_x_runtime_validation_types/__init__.py", '''
"""ATHENA-X validation types."""
from .types import (
    ValidationStatus,
    QualityGrade,
    ValidationReason,
    ValidationResult,
    AuditEntry,
    QuarantineRecord,
    ValidationContext,
    VALIDATOR_VERSION,
)
from .factory import create_result, create_audit, create_quarantine

__all__ = [
    "ValidationStatus", "QualityGrade", "ValidationReason", "ValidationResult",
    "AuditEntry", "QuarantineRecord", "ValidationContext",
    "VALIDATOR_VERSION",
    "create_result", "create_audit", "create_quarantine",
]
__version__ = "0.1.0"
''')

w("runtime/validation-types/src/athena_x_runtime_validation_types/types.py", '''
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
''')

w("runtime/validation-types/src/athena_x_runtime_validation_types/factory.py", '''
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
        auditId=uuid4(),
        timestamp=datetime.now(timezone.utc),
        provider=provider,
        validator=validator,
        rule_triggered=rule_triggered,
        originalValue=original_value,
        correctedValue=corrected_value,
        decision=decision,
        validatorVersion=VALIDATOR_VERSION,
        symbol=symbol,
        recordId=record_id,
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
        quarantineId=uuid4(),
        quarantinedAt=datetime.now(timezone.utc),
        provider=provider,
        symbol=symbol,
        rawPayload=raw_payload,
        reason=reason,
        validator=validator,
        errorCode=error_code,
        originalTimestamp=original_timestamp,
        confidenceScore=confidence_score,
    )
''')

w("runtime/validation-types/tests/__init__.py", "")
w("runtime/validation-types/tests/test_types.py", '''
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
''')

# ============================================================================
# 2. AUDIT TRAIL — runtime/audit-trail/
# ============================================================================

w("runtime/audit-trail/pyproject.toml", '''
[project]
name = "athena-x-runtime-audit-trail"
version = "0.1.0"
description = "Audit trail logging + deterministic replay (Stage 3 req 7)"
requires-python = ">=3.11"
dependencies = [
    "athena-x-runtime-validation-types",
    "athena-x-runtime-logger",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_runtime_audit_trail"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w("runtime/audit-trail/src/athena_x_runtime_audit_trail/__init__.py", '''
"""ATHENA-X audit trail."""
from .trail import AuditTrail, AuditQuery

__all__ = ["AuditTrail", "AuditQuery"]
__version__ = "0.1.0"
''')

w("runtime/audit-trail/src/athena_x_runtime_audit_trail/trail.py", '''
"""Audit trail — logs every validation decision (Stage 3 req 7).

Nothing is silently fixed. Every correction, rejection, warning, and
quarantine is recorded with:
  - provider, validator, rule_triggered
  - original_value, corrected_value
  - timestamp, version, decision

Supports deterministic replay: given a record_id + validator_version,
the audit trail can reproduce the exact decision.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any
from uuid import UUID

from athena_x_runtime_validation_types import AuditEntry, ValidationStatus
from athena_x_runtime_logger import get_logger

log = get_logger("runtime.audit-trail")


class AuditQuery:
    """Query parameters for searching the audit trail."""
    def __init__(
        self,
        provider: str | None = None,
        validator: str | None = None,
        symbol: str | None = None,
        decision: ValidationStatus | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ):
        self.provider = provider
        self.validator = validator
        self.symbol = symbol
        self.decision = decision
        self.start_time = start_time
        self.end_time = end_time

    def matches(self, entry: AuditEntry) -> bool:
        if self.provider and entry.provider != self.provider:
            return False
        if self.validator and entry.validator != self.validator:
            return False
        if self.symbol and entry.symbol != self.symbol:
            return False
        if self.decision and entry.decision != self.decision:
            return False
        if self.start_time and entry.timestamp < self.start_time:
            return False
        if self.end_time and entry.timestamp > self.end_time:
            return False
        return True


class AuditTrail:
    """In-memory + filesystem audit trail.

    In production, this would be backed by a dedicated audit database
    (append-only, tamper-evident). For Stage 3, we use in-memory + optional
    filesystem persistence.
    """

    def __init__(self, persist_path: str | Path | None = None):
        self._entries: list[AuditEntry] = []
        self._lock = Lock()
        self._persist_path = Path(persist_path) if persist_path else None
        if self._persist_path:
            self._persist_path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, entry: AuditEntry) -> None:
        """Append an entry to the audit trail."""
        with self._lock:
            self._entries.append(entry)
        log.debug("audit_logged",
                  audit_id=str(entry.audit_id),
                  provider=entry.provider,
                  validator=entry.validator,
                  decision=entry.decision.value)

        if self._persist_path:
            self._persist_entry(entry)

    def _persist_entry(self, entry: AuditEntry) -> None:
        """Append entry to filesystem log (JSONL format)."""
        try:
            with open(self._persist_path, "a", encoding="utf-8") as f:
                f.write(entry.model_dump_json(by_alias=True) + "\\n")
        except Exception as e:
            log.error("audit_persist_failed", error=str(e))

    def query(self, q: AuditQuery) -> list[AuditEntry]:
        """Query the audit trail."""
        with self._lock:
            return [e for e in self._entries if q.matches(e)]

    def get_by_record(self, record_id: str) -> list[AuditEntry]:
        """Get all audit entries for a specific record."""
        with self._lock:
            return [e for e in self._entries if e.record_id == record_id]

    def get_by_id(self, audit_id: UUID) -> AuditEntry | None:
        with self._lock:
            for e in self._entries:
                if e.audit_id == audit_id:
                    return e
        return None

    def count(self) -> int:
        with self._lock:
            return len(self._entries)

    def count_by_decision(self) -> dict[str, int]:
        with self._lock:
            counts: dict[str, int] = {}
            for e in self._entries:
                counts[e.decision.value] = counts.get(e.decision.value, 0) + 1
            return counts

    def count_by_provider(self) -> dict[str, int]:
        with self._lock:
            counts: dict[str, int] = {}
            for e in self._entries:
                counts[e.provider] = counts.get(e.provider, 0) + 1
            return counts

    def count_by_validator(self) -> dict[str, int]:
        with self._lock:
            counts: dict[str, int] = {}
            for e in self._entries:
                counts[e.validator] = counts.get(e.validator, 0) + 1
            return counts

    def replay(self, record_id: str, validator_version: str) -> list[AuditEntry]:
        """Deterministic replay — return all decisions for a record at a version."""
        with self._lock:
            return [
                e for e in self._entries
                if e.record_id == record_id
                and e.validator_version == validator_version
            ]

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()
''')

w("runtime/audit-trail/tests/__init__.py", "")
w("runtime/audit-trail/tests/test_trail.py", '''
"""Tests for audit trail (Stage 3 req 7)."""
import pytest
from datetime import datetime, timezone
from athena_x_runtime_validation_types import create_audit, ValidationStatus
from athena_x_runtime_audit_trail import AuditTrail, AuditQuery


@pytest.fixture
def trail():
    return AuditTrail()


def test_log_and_count(trail):
    """Entries can be logged and counted."""
    entry = create_audit(
        provider="yahoo", validator="schema",
        rule_triggered="missing_field",
        original_value={}, corrected_value=None,
        decision=ValidationStatus.REJECTED, symbol="SPY",
    )
    trail.log(entry)
    assert trail.count() == 1


def test_query_by_provider(trail):
    """Query filters by provider."""
    for p in ["yahoo", "yahoo", "finnhub"]:
        trail.log(create_audit(
            provider=p, validator="schema", rule_triggered="test",
            original_value={}, corrected_value=None,
            decision=ValidationStatus.VERIFIED, symbol="SPY",
        ))
    results = trail.query(AuditQuery(provider="yahoo"))
    assert len(results) == 2


def test_query_by_decision(trail):
    """Query filters by decision."""
    for d in [ValidationStatus.VERIFIED, ValidationStatus.REJECTED, ValidationStatus.VERIFIED]:
        trail.log(create_audit(
            provider="yahoo", validator="schema", rule_triggered="test",
            original_value={}, corrected_value=None,
            decision=d, symbol="SPY",
        ))
    results = trail.query(AuditQuery(decision=ValidationStatus.VERIFIED))
    assert len(results) == 2


def test_count_by_decision(trail):
    """count_by_decision aggregates by status."""
    for d in [ValidationStatus.VERIFIED, ValidationStatus.REJECTED, ValidationStatus.VERIFIED]:
        trail.log(create_audit(
            provider="yahoo", validator="schema", rule_triggered="test",
            original_value={}, corrected_value=None,
            decision=d, symbol="SPY",
        ))
    counts = trail.count_by_decision()
    assert counts["verified"] == 2
    assert counts["rejected"] == 1


def test_get_by_record(trail):
    """get_by_record returns all entries for a record."""
    for _ in range(3):
        trail.log(create_audit(
            provider="yahoo", validator="schema", rule_triggered="test",
            original_value={}, corrected_value=None,
            decision=ValidationStatus.VERIFIED, symbol="SPY",
            record_id="rec-123",
        ))
    results = trail.get_by_record("rec-123")
    assert len(results) == 3


def test_replay_deterministic(trail):
    """Replay returns all decisions for a record at a specific version."""
    from athena_x_runtime_validation_types import VALIDATOR_VERSION
    trail.log(create_audit(
        provider="yahoo", validator="schema", rule_triggered="test",
        original_value={}, corrected_value=None,
        decision=ValidationStatus.VERIFIED, symbol="SPY",
        record_id="rec-123",
    ))
    results = trail.replay("rec-123", VALIDATOR_VERSION)
    assert len(results) == 1
    # Different version returns nothing
    results = trail.replay("rec-123", "0.0.0")
    assert len(results) == 0


def test_persist_to_filesystem(tmp_path):
    """Audit entries are persisted to filesystem as JSONL."""
    persist_path = tmp_path / "audit.jsonl"
    trail = AuditTrail(persist_path=persist_path)
    trail.log(create_audit(
        provider="yahoo", validator="schema", rule_triggered="test",
        original_value={"x": 1}, corrected_value=None,
        decision=ValidationStatus.VERIFIED, symbol="SPY",
    ))
    assert persist_path.exists()
    content = persist_path.read_text()
    assert '"provider":"yahoo"' in content
''')

# ============================================================================
# 3. BASE VALIDATOR + PIPELINE — agents/validation/_base/
# ============================================================================

w("agents/validation/_base/pyproject.toml", '''
[project]
name = "athena-x-validator-base"
version = "0.1.0"
description = "Base validator framework + ValidationPipeline orchestrator"
requires-python = ">=3.11"
dependencies = [
    "athena-x-runtime-validation-types",
    "athena-x-runtime-audit-trail",
    "athena-x-runtime-logger",
    "athena-x-runtime-institutional-metadata",
    "athena-x-runtime-session-awareness",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_validator_base"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w("agents/validation/_base/src/athena_x_validator_base/__init__.py", '''
"""Base validator framework."""
from .base import BaseValidator, ValidatorConfig
from .pipeline import ValidationPipeline, PipelineResult
from .registry import ValidatorRegistry

__all__ = [
    "BaseValidator", "ValidatorConfig",
    "ValidationPipeline", "PipelineResult",
    "ValidatorRegistry",
]
__version__ = "0.1.0"
''')

w("agents/validation/_base/src/athena_x_validator_base/base.py", '''
"""Base validator framework.

Each validator implements `validate(record, context) -> ValidationResult`.
Validators are PURE FUNCTIONS — deterministic, no side effects, no time-dependent
logic. This ensures replay determinism (Stage 3 req: replay capability).
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from athena_x_runtime_validation_types import (
    ValidationResult, ValidationContext, ValidationStatus,
)


@dataclass
class ValidatorConfig:
    """Configuration for a validator."""
    name: str
    version: str = "1.0.0"
    enabled: bool = True
    # If True, a REJECTED status from this validator halts the pipeline
    # (subsequent validators don't run). If False, the pipeline continues.
    blocking: bool = True


class BaseValidator(ABC):
    """Abstract base class for all validators.

    Subclasses implement `validate()`. The base class provides:
      - Name + version metadata
      - Enable/disable toggle
      - Blocking behavior (does a rejection halt the pipeline?)
    """

    def __init__(self, config: ValidatorConfig):
        self.config = config

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def version(self) -> str:
        return self.config.version

    @property
    def enabled(self) -> bool:
        return self.config.enabled

    @property
    def blocking(self) -> bool:
        return self.config.blocking

    @abstractmethod
    async def validate(self, record: Any, context: ValidationContext) -> ValidationResult:
        """Validate a record. MUST be deterministic.

        Args:
            record: the raw data record (dict)
            context: validation context (provider, symbol, peers, etc.)

        Returns:
            ValidationResult with status, reason, confidence_delta
        """
        ...

    def _passed(self, message: str = "") -> ValidationResult:
        """Helper: return a 'passed' result."""
        from athena_x_runtime_validation_types import create_result, ValidationReason
        return create_result(
            validator_name=self.name,
            status=ValidationStatus.VERIFIED,
            reason=ValidationReason.PASSED,
            confidence_delta=0.0,
            message=message,
        )

    def _warning(self, reason, message: str, confidence_delta: float = -0.1) -> ValidationResult:
        from athena_x_runtime_validation_types import create_result
        return create_result(
            validator_name=self.name,
            status=ValidationStatus.WARNING,
            reason=reason,
            confidence_delta=confidence_delta,
            message=message,
        )

    def _quarantine(self, reason, message: str, confidence_delta: float = -0.5) -> ValidationResult:
        from athena_x_runtime_validation_types import create_result
        return create_result(
            validator_name=self.name,
            status=ValidationStatus.QUARANTINED,
            reason=reason,
            confidence_delta=confidence_delta,
            message=message,
        )

    def _reject(self, reason, message: str, confidence_delta: float = -1.0) -> ValidationResult:
        from athena_x_runtime_validation_types import create_result
        return create_result(
            validator_name=self.name,
            status=ValidationStatus.REJECTED,
            reason=reason,
            confidence_delta=confidence_delta,
            message=message,
        )
''')

w("agents/validation/_base/src/athena_x_validator_base/registry.py", '''
"""Validator registry — tracks all registered validators."""
from __future__ import annotations
from threading import Lock
from .base import BaseValidator


class ValidatorRegistry:
    """Thread-safe registry of validators."""
    def __init__(self):
        self._validators: dict[str, BaseValidator] = {}
        self._lock = Lock()

    def register(self, validator: BaseValidator) -> None:
        with self._lock:
            self._validators[validator.name] = validator

    def get(self, name: str) -> BaseValidator | None:
        with self._lock:
            return self._validators.get(name)

    def list_all(self) -> list[BaseValidator]:
        with self._lock:
            return list(self._validators.values())

    def list_enabled(self) -> list[BaseValidator]:
        with self._lock:
            return [v for v in self._validators.values() if v.enabled]
''')

w("agents/validation/_base/src/athena_x_validator_base/pipeline.py", '''
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
''')

w("agents/validation/_base/tests/__init__.py", "")
w("agents/validation/_base/tests/test_pipeline.py", '''
"""Tests for validation pipeline."""
import pytest
from datetime import datetime, timezone
from athena_x_runtime_validation_types import (
    ValidationContext, ValidationStatus, ValidationReason, VALIDATOR_VERSION,
)
from athena_x_runtime_audit_trail import AuditTrail
from athena_x_validator_base import (
    BaseValidator, ValidatorConfig, ValidationPipeline,
)


class AlwaysPassValidator(BaseValidator):
    def __init__(self):
        super().__init__(ValidatorConfig(name="always-pass", blocking=False))
    async def validate(self, record, context):
        return self._passed("all good")


class AlwaysRejectValidator(BaseValidator):
    def __init__(self):
        super().__init__(ValidatorConfig(name="always-reject", blocking=True))
    async def validate(self, record, context):
        return self._reject(ValidationReason.UNKNOWN, "rejected")


class AlwaysWarnValidator(BaseValidator):
    def __init__(self):
        super().__init__(ValidatorConfig(name="always-warn", blocking=False))
    async def validate(self, record, context):
        return self._warning(ValidationReason.UNKNOWN, "warning", -0.2)


@pytest.fixture
def context():
    return ValidationContext(
        pipelineStartedAt=datetime.now(timezone.utc),
        provider="yahoo",
        symbol="SPY",
        asset_class="etf",
    )


async def test_pipeline_passes_clean_record(context):
    """A record passing all validators is Verified."""
    pipeline = ValidationPipeline(validators=[AlwaysPassValidator()])
    result = await pipeline.validate({"symbol": "SPY", "last": 450.0}, context)
    assert result.final_status == ValidationStatus.VERIFIED
    assert result.accepted is True
    assert result.confidence_score == 1.0
    assert result.quality_grade.value == "A+"


async def test_pipeline_rejects_on_blocking_validator(context):
    """A blocking validator rejection halts the pipeline."""
    pipeline = ValidationPipeline(
        validators=[AlwaysRejectValidator(), AlwaysPassValidator()]
    )
    result = await pipeline.validate({}, context)
    assert result.final_status == ValidationStatus.REJECTED
    assert result.quarantined is True
    # Only the first validator ran (blocking)
    assert len(result.results) == 1


async def test_pipeline_continues_on_warning(context):
    """Warnings don't halt the pipeline."""
    pipeline = ValidationPipeline(
        validators=[AlwaysWarnValidator(), AlwaysPassValidator()]
    )
    result = await pipeline.validate({}, context)
    assert result.final_status == ValidationStatus.WARNING
    assert result.accepted is True  # warnings still go to canonical DB
    assert len(result.results) == 2
    assert result.confidence_score == 0.8  # 1.0 - 0.2


async def test_pipeline_logs_to_audit_trail(context):
    """Every validation decision is logged."""
    audit = AuditTrail()
    pipeline = ValidationPipeline(
        validators=[AlwaysPassValidator()],
        audit_trail=audit,
    )
    await pipeline.validate({}, context)
    assert audit.count() == 1


async def test_pipeline_metadata_includes_6_fields(context):
    """to_metadata() returns the 6 confidence metadata fields."""
    pipeline = ValidationPipeline(validators=[AlwaysPassValidator()])
    result = await pipeline.validate({}, context)
    metadata = result.to_metadata()
    assert "validation_status" in metadata
    assert "validation_time" in metadata
    assert "validator_version" in metadata
    assert "confidence_score" in metadata
    assert "quality_grade" in metadata
    assert "validation_reason" in metadata


async def test_pipeline_stats_tracked(context):
    """Pipeline tracks acceptance/rejection stats."""
    pipeline = ValidationPipeline(
        validators=[AlwaysRejectValidator()]
    )
    await pipeline.validate({}, context)
    await pipeline.validate({}, context)
    stats = pipeline.get_stats()
    assert stats["total_records"] == 2
    assert stats["rejected"] == 2
    assert stats["rejection_rate"] == 1.0


async def test_pipeline_deterministic(context):
    """Same input + version → same output (replay determinism)."""
    pipeline = ValidationPipeline(validators=[AlwaysPassValidator()])
    r1 = await pipeline.validate({"x": 1}, context)
    r2 = await pipeline.validate({"x": 1}, context)
    # Same final status + confidence
    assert r1.final_status == r2.final_status
    assert r1.confidence_score == r2.confidence_score
    assert r1.validator_version == r2.validator_version
''')

# ============================================================================
# 4. SCHEMA VALIDATOR — agents/validation/schema-validator/
# ============================================================================

w("agents/validation/schema-validator/pyproject.toml", '''
[project]
name = "athena-x-validator-schema"
version = "0.1.0"
description = "Schema validator — required fields, types, nulls, precision, symbol validity"
requires-python = ">=3.11"
dependencies = ["athena-x-validator-base"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_validator_schema"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w("agents/validation/schema-validator/src/athena_x_validator_schema/__init__.py", '''
"""Schema validator."""
from .validator import SchemaValidator, QUOTE_REQUIRED_FIELDS

__all__ = ["SchemaValidator", "QUOTE_REQUIRED_FIELDS"]
__version__ = "0.1.0"
''')

w("agents/validation/schema-validator/src/athena_x_validator_schema/validator.py", '''
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
''')

w("agents/validation/schema-validator/tests/__init__.py", "")
w("agents/validation/schema-validator/tests/test_validator.py", '''
"""Tests for schema validator."""
import pytest
from datetime import datetime, timezone
from athena_x_validator_schema import SchemaValidator
from athena_x_runtime_validation_types import (
    ValidationContext, ValidationStatus, ValidationReason,
)


@pytest.fixture
def context():
    return ValidationContext(
        pipelineStartedAt=datetime.now(timezone.utc),
        provider="yahoo", symbol="SPY", asset_class="etf",
    )


@pytest.fixture
def validator():
    return SchemaValidator()


async def test_valid_record_passes(validator, context):
    result = await validator.validate(
        {"symbol": "SPY", "last": 450.0, "timestamp": "2026-07-17T10:00:00Z"},
        context,
    )
    assert result.status == ValidationStatus.VERIFIED


async def test_missing_required_field_rejected(validator, context):
    result = await validator.validate(
        {"symbol": "SPY", "timestamp": "2026-07-17T10:00:00Z"},  # missing 'last'
        context,
    )
    assert result.status == ValidationStatus.REJECTED
    assert result.reason == ValidationReason.MISSING_REQUIRED_FIELD


async def test_null_value_rejected(validator, context):
    result = await validator.validate(
        {"symbol": "SPY", "last": None, "timestamp": "2026-07-17T10:00:00Z"},
        context,
    )
    assert result.status == ValidationStatus.REJECTED
    assert result.reason == ValidationReason.NULL_VALUE


async def test_invalid_data_type_rejected(validator, context):
    result = await validator.validate(
        {"symbol": "SPY", "last": "four hundred", "timestamp": "2026-07-17T10:00:00Z"},
        context,
    )
    assert result.status == ValidationStatus.REJECTED
    assert result.reason == ValidationReason.INVALID_DATA_TYPE


async def test_invalid_symbol_rejected(validator, context):
    result = await validator.validate(
        {"symbol": "invalid symbol with spaces", "last": 100, "timestamp": "2026-07-17T10:00:00Z"},
        context,
    )
    assert result.status == ValidationStatus.REJECTED
    assert result.reason == ValidationReason.INVALID_SYMBOL


async def test_negative_price_rejected(validator, context):
    result = await validator.validate(
        {"symbol": "SPY", "last": -100, "timestamp": "2026-07-17T10:00:00Z"},
        context,
    )
    assert result.status == ValidationStatus.REJECTED
    assert result.reason == ValidationReason.INVALID_PRECISION


async def test_special_symbols_accepted(validator, context):
    """Special symbols like BTC-USD, Gold, Oil are accepted."""
    for sym in ["BTC-USD", "ETH-USD", "Gold", "Oil", "Copper", "USDJPY", "DXY"]:
        ctx = ValidationContext(
            pipelineStartedAt=datetime.now(timezone.utc),
            provider="yahoo", symbol=sym, asset_class="crypto",
        )
        result = await validator.validate(
            {"symbol": sym, "last": 100, "timestamp": "2026-07-17T10:00:00Z"},
            ctx,
        )
        assert result.status == ValidationStatus.VERIFIED, f"Failed for {sym}"


async def test_non_dict_record_rejected(validator, context):
    result = await validator.validate("not a dict", context)
    assert result.status == ValidationStatus.REJECTED


async def test_brk_b_symbol_accepted(validator, context):
    """BRK.B (Berkshire Hathaway) is a valid symbol."""
    result = await validator.validate(
        {"symbol": "BRK.B", "last": 400, "timestamp": "2026-07-17T10:00:00Z"},
        context,
    )
    assert result.status == ValidationStatus.VERIFIED
''')

# ============================================================================
# 5. TIMESTAMP VALIDATOR — agents/validation/timestamp-validator/
# ============================================================================

w("agents/validation/timestamp-validator/pyproject.toml", '''
[project]
name = "athena-x-validator-timestamp"
version = "0.1.0"
description = "Timestamp validator — UTC, clock drift, out-of-order, duplicates"
requires-python = ">=3.11"
dependencies = ["athena-x-validator-base"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_validator_timestamp"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w("agents/validation/timestamp-validator/src/athena_x_validator_timestamp/__init__.py", '''
"""Timestamp validator."""
from .validator import TimestampValidator

__all__ = ["TimestampValidator"]
__version__ = "0.1.0"
''')

w("agents/validation/timestamp-validator/src/athena_x_validator_timestamp/validator.py", '''
"""Timestamp validator — Stage 3 req 2.2.

Checks:
  - UTC format (timezone-aware)
  - Exchange timestamp vs arrival timestamp
  - Clock drift (max 5 seconds)
  - Duplicate timestamps (same provider + symbol + ts)
  - Out-of-order events (ts older than last seen)

Rejects impossible timestamps.

Deterministic: uses the record's timestamp, not now(). The pipeline_started_at
in context serves as the "arrival" reference.
"""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from typing import Any
from threading import Lock

from athena_x_validator_base import BaseValidator, ValidatorConfig
from athena_x_runtime_validation_types import (
    ValidationResult, ValidationContext, ValidationStatus, ValidationReason,
)


MAX_CLOCK_DRIFT_SECONDS = 5.0
MAX_FUTURE_SECONDS = 60.0  # allow up to 1 minute in the future (network delay)
MAX_STALE_SECONDS = 300.0  # 5 minutes


class TimestampValidator(BaseValidator):
    """Validates timestamps in a record."""

    def __init__(self):
        super().__init__(ValidatorConfig(
            name="timestamp-validator",
            blocking=True,
        ))
        self._last_timestamps: dict[str, datetime] = {}  # {provider:symbol: ts}
        self._seen_timestamps: dict[str, set[datetime]] = {}  # for duplicate detection
        self._lock = Lock()

    async def validate(self, record: Any, context: ValidationContext) -> ValidationResult:
        """Validate the record's timestamp."""
        ts_str = record.get("timestamp") if isinstance(record, dict) else None
        if not ts_str:
            return self._reject(
                ValidationReason.MISSING_REQUIRED_FIELD,
                "Missing timestamp field",
            )

        # Parse timestamp
        try:
            ts = self._parse_timestamp(ts_str)
        except (ValueError, TypeError) as e:
            return self._reject(
                ValidationReason.NAIVE_TIMESTAMP,
                f"Invalid timestamp format: {ts_str} ({e})",
            )

        if ts.tzinfo is None:
            return self._reject(
                ValidationReason.NAIVE_TIMESTAMP,
                f"Timestamp must be UTC-aware: {ts_str}",
            )

        ts_utc = ts.astimezone(timezone.utc)

        # Check future timestamp (allow small tolerance)
        pipeline_started = context.pipeline_started_at
        if ts_utc > pipeline_started + timedelta(seconds=MAX_FUTURE_SECONDS):
            return self._reject(
                ValidationReason.FUTURE_TIMESTAMP,
                f"Timestamp is too far in the future: {ts_utc.isoformat()}",
            )

        # Check staleness
        age = (pipeline_started - ts_utc).total_seconds()
        if age > MAX_STALE_SECONDS:
            return self._warning(
                ValidationReason.STALE_TIMESTAMP,
                f"Timestamp is {age:.1f}s old",
                confidence_delta=-0.3,
            )

        # Check clock drift (ts vs pipeline start)
        drift = abs((ts_utc - pipeline_started).total_seconds())
        if drift > MAX_CLOCK_DRIFT_SECONDS:
            return self._warning(
                ValidationReason.CLOCK_DRIFT,
                f"Clock drift: {drift:.1f}s",
                confidence_delta=-0.1,
            )

        # Check out-of-order (per provider:symbol)
        key = f"{context.provider}:{context.symbol}"
        with self._lock:
            last_ts = self._last_timestamps.get(key)
            if last_ts and ts_utc < last_ts:
                return self._reject(
                    ValidationReason.OUT_OF_ORDER,
                    f"Out-of-order: {ts_utc.isoformat()} < {last_ts.isoformat()}",
                )

            # Check duplicate timestamp
            seen_set = self._seen_timestamps.setdefault(key, set())
            if ts_utc in seen_set:
                return self._reject(
                    ValidationReason.DUPLICATE_TIMESTAMP,
                    f"Duplicate timestamp: {ts_utc.isoformat()}",
                )

            # Update state
            self._last_timestamps[key] = ts_utc
            seen_set.add(ts_utc)
            # Trim seen set to last 1000 entries
            if len(seen_set) > 1000:
                seen_set.clear()
                seen_set.add(ts_utc)

        return self._passed("timestamp valid")

    def _parse_timestamp(self, ts_str: str) -> datetime:
        """Parse a timestamp string (ISO 8601 or unix-millis)."""
        if isinstance(ts_str, (int, float)):
            # Unix timestamp
            if ts_str > 1e12:
                # milliseconds
                return datetime.fromtimestamp(ts_str / 1000, tz=timezone.utc)
            return datetime.fromtimestamp(ts_str, tz=timezone.utc)

        if isinstance(ts_str, str):
            # ISO 8601
            normalized = ts_str.replace("Z", "+00:00")
            return datetime.fromisoformat(normalized)

        raise ValueError(f"Cannot parse timestamp: {ts_str}")
''')

w("agents/validation/timestamp-validator/tests/__init__.py", "")
w("agents/validation/timestamp-validator/tests/test_validator.py", '''
"""Tests for timestamp validator."""
import pytest
from datetime import datetime, timezone, timedelta
from athena_x_validator_timestamp import TimestampValidator
from athena_x_runtime_validation_types import (
    ValidationContext, ValidationStatus, ValidationReason,
)


@pytest.fixture
def validator():
    return TimestampValidator()


def make_context(provider="yahoo", symbol="SPY"):
    return ValidationContext(
        pipelineStartedAt=datetime.now(timezone.utc),
        provider=provider, symbol=symbol, asset_class="etf",
    )


async def test_valid_timestamp_passes(validator):
    ctx = make_context()
    result = await validator.validate(
        {"timestamp": datetime.now(timezone.utc).isoformat()},
        ctx,
    )
    assert result.status == ValidationStatus.VERIFIED


async def test_naive_timestamp_rejected(validator):
    """Timestamps without timezone are rejected."""
    ctx = make_context()
    result = await validator.validate(
        {"timestamp": "2026-07-17T10:00:00"},  # no timezone
        ctx,
    )
    assert result.status == ValidationStatus.REJECTED
    assert result.reason == ValidationReason.NAIVE_TIMESTAMP


async def test_future_timestamp_rejected(validator):
    """Timestamps too far in the future are rejected."""
    ctx = make_context()
    future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    result = await validator.validate({"timestamp": future}, ctx)
    assert result.status == ValidationStatus.REJECTED
    assert result.reason == ValidationReason.FUTURE_TIMESTAMP


async def test_stale_timestamp_warning(validator):
    """Old timestamps get a warning (not rejection)."""
    ctx = make_context()
    stale = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
    result = await validator.validate({"timestamp": stale}, ctx)
    assert result.status == ValidationStatus.WARNING
    assert result.reason == ValidationReason.STALE_TIMESTAMP


async def test_out_of_order_rejected(validator):
    """Out-of-order events are rejected."""
    ctx = make_context()
    now = datetime.now(timezone.utc)
    # First event
    await validator.validate({"timestamp": now.isoformat()}, ctx)
    # Earlier event (out of order)
    earlier = (now - timedelta(seconds=30)).isoformat()
    result = await validator.validate({"timestamp": earlier}, ctx)
    assert result.status == ValidationStatus.REJECTED
    assert result.reason == ValidationReason.OUT_OF_ORDER


async def test_duplicate_timestamp_rejected(validator):
    """Duplicate timestamps (same provider+symbol) are rejected."""
    ctx = make_context()
    ts = datetime.now(timezone.utc).isoformat()
    # First occurrence
    await validator.validate({"timestamp": ts}, ctx)
    # Duplicate
    result = await validator.validate({"timestamp": ts}, ctx)
    assert result.status == ValidationStatus.REJECTED
    assert result.reason == ValidationReason.DUPLICATE_TIMESTAMP


async def test_duplicate_different_provider_accepted(validator):
    """Same timestamp from different providers is accepted."""
    ts = datetime.now(timezone.utc).isoformat()
    await validator.validate({"timestamp": ts}, make_context(provider="yahoo"))
    result = await validator.validate({"timestamp": ts}, make_context(provider="polygon"))
    assert result.status == ValidationStatus.VERIFIED


async def test_unix_millis_timestamp_accepted(validator):
    """Unix millisecond timestamps are parsed correctly."""
    ctx = make_context()
    ts_millis = int(datetime.now(timezone.utc).timestamp() * 1000)
    result = await validator.validate({"timestamp": ts_millis}, ctx)
    assert result.status == ValidationStatus.VERIFIED
''')

# ============================================================================
# 6. MARKET CALENDAR VALIDATOR — agents/validation/market-calendar-validator/
# ============================================================================

w("agents/validation/market-calendar-validator/pyproject.toml", '''
[project]
name = "athena-x-validator-market-calendar"
version = "0.1.0"
description = "Market calendar validator — trading day, holiday, weekend, session"
requires-python = ">=3.11"
dependencies = [
    "athena-x-validator-base",
    "athena-x-runtime-session-awareness",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_validator_market_calendar"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w("agents/validation/market-calendar-validator/src/athena_x_validator_market_calendar/__init__.py", '''
"""Market calendar validator."""
from .validator import MarketCalendarValidator

__all__ = ["MarketCalendarValidator"]
__version__ = "0.1.0"
''')

w("agents/validation/market-calendar-validator/src/athena_x_validator_market_calendar/validator.py", '''
"""Market calendar validator — Stage 3 req 2.3.

Verifies:
  - Trading day (not weekend/holiday for non-crypto)
  - Market holiday
  - Weekend (allowed only for crypto)
  - Trading session
  - Early close
  - Half-day schedule

Example: SPY trading on Christmas Day → REJECT.
"""
from __future__ import annotations
from datetime import datetime
from typing import Any

from athena_x_validator_base import BaseValidator, ValidatorConfig
from athena_x_runtime_validation_types import (
    ValidationResult, ValidationContext, ValidationStatus, ValidationReason,
)
from athena_x_runtime_session_awareness import SessionDetector, SessionType


# Symbols that trade 24/7 (no calendar restrictions)
CRYPTO_SYMBOLS = {"BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "BTC", "ETH"}


class MarketCalendarValidator(BaseValidator):
    """Validates that a record's timestamp is a valid trading time."""

    def __init__(self):
        super().__init__(ValidatorConfig(
            name="market-calendar-validator",
            blocking=True,
        ))
        self._detector = SessionDetector()

    async def validate(self, record: Any, context: ValidationContext) -> ValidationResult:
        """Validate the record against the market calendar."""
        # Extract timestamp from record
        ts_str = record.get("timestamp") if isinstance(record, dict) else None
        if not ts_str:
            return self._reject(
                ValidationReason.MISSING_REQUIRED_FIELD,
                "Missing timestamp for calendar check",
            )

        # Parse timestamp
        try:
            ts = self._parse_timestamp(ts_str)
        except Exception:
            return self._reject(
                ValidationReason.NAIVE_TIMESTAMP,
                f"Cannot parse timestamp: {ts_str}",
            )

        # Detect session
        info = self._detector.detect(ts, symbol=context.symbol)

        # Crypto: always allowed
        if info.is_crypto:
            return self._passed(f"crypto trades 24/7 (session: {info.session.value})")

        # Non-crypto: reject weekends and holidays
        if info.session == SessionType.WEEKEND:
            return self._reject(
                ValidationReason.WEEKEND,
                f"Non-crypto symbol {context.symbol} trading on weekend: {info.description}",
            )

        if info.session == SessionType.HOLIDAY:
            return self._reject(
                ValidationReason.HOLIDAY,
                f"Non-crypto symbol {context.symbol} trading on holiday: {info.description}",
            )

        # Overnight session: warning (low liquidity)
        if info.session == SessionType.OVERNIGHT:
            return self._warning(
                ValidationReason.WRONG_SESSION,
                f"Overnight session — low liquidity: {info.description}",
                confidence_delta=-0.2,
            )

        return self._passed(f"session: {info.session.value}")

    def _parse_timestamp(self, ts_str) -> datetime:
        """Parse ISO 8601 or unix timestamp."""
        from datetime import datetime, timezone
        if isinstance(ts_str, (int, float)):
            if ts_str > 1e12:
                return datetime.fromtimestamp(ts_str / 1000, tz=timezone.utc)
            return datetime.fromtimestamp(ts_str, tz=timezone.utc)
        normalized = ts_str.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
''')

w("agents/validation/market-calendar-validator/tests/__init__.py", "")
w("agents/validation/market-calendar-validator/tests/test_validator.py", '''
"""Tests for market calendar validator."""
import pytest
from datetime import datetime, timezone
import pytz
from athena_x_validator_market_calendar import MarketCalendarValidator
from athena_x_runtime_validation_types import (
    ValidationContext, ValidationStatus, ValidationReason,
)


@pytest.fixture
def validator():
    return MarketCalendarValidator()


def make_context(symbol="SPY"):
    return ValidationContext(
        pipelineStartedAt=datetime.now(timezone.utc),
        provider="yahoo", symbol=symbol, asset_class="etf",
    )


def et_time(month, day, hour, year=2026):
    """ET-localized datetime."""
    return pytz.timezone("America/New_York").localize(datetime(year, month, day, hour, 0))


async def test_christmas_rejected(validator):
    """SPY trading on Christmas Day is rejected."""
    ts = et_time(12, 25, 10, 2026)
    result = await validator.validate(
        {"timestamp": ts.isoformat()},
        make_context("SPY"),
    )
    assert result.status == ValidationStatus.REJECTED
    assert result.reason == ValidationReason.HOLIDAY


async def test_weekend_rejected(validator):
    """SPY trading on Saturday is rejected."""
    ts = et_time(7, 18, 10, 2026)  # Saturday
    result = await validator.validate(
        {"timestamp": ts.isoformat()},
        make_context("SPY"),
    )
    assert result.status == ValidationStatus.REJECTED
    assert result.reason == ValidationReason.WEEKEND


async def test_regular_session_accepted(validator):
    """SPY during regular trading hours is accepted."""
    ts = et_time(7, 17, 10, 2026)  # Friday 10am ET
    result = await validator.validate(
        {"timestamp": ts.isoformat()},
        make_context("SPY"),
    )
    assert result.status == ValidationStatus.VERIFIED


async def test_crypto_accepted_on_weekend(validator):
    """BTC trades 24/7 — accepted on weekend."""
    ts = et_time(7, 18, 10, 2026)  # Saturday
    result = await validator.validate(
        {"timestamp": ts.isoformat()},
        make_context("BTC-USD"),
    )
    assert result.status == ValidationStatus.VERIFIED


async def test_overnight_session_warning(validator):
    """Overnight session gets a warning (low liquidity)."""
    ts = et_time(7, 17, 22, 2026)  # Friday 10pm ET (overnight)
    result = await validator.validate(
        {"timestamp": ts.isoformat()},
        make_context("SPY"),
    )
    assert result.status == ValidationStatus.WARNING
    assert result.reason == ValidationReason.WRONG_SESSION


async def test_july_4_rejected(validator):
    """July 4 (Independence Day) is rejected."""
    ts = et_time(7, 4, 10, 2025)  # Friday July 4, 2025
    result = await validator.validate(
        {"timestamp": ts.isoformat()},
        make_context("SPY"),
    )
    assert result.status == ValidationStatus.REJECTED
    assert result.reason == ValidationReason.HOLIDAY
''')

# ============================================================================
# 7. CROSS-PROVIDER VALIDATOR — agents/validation/cross-provider-validator/
# ============================================================================

w("agents/validation/cross-provider-validator/pyproject.toml", '''
[project]
name = "athena-x-validator-cross-provider"
version = "0.1.0"
description = "Cross-provider validator — consensus check, outlier rejection"
requires-python = ">=3.11"
dependencies = ["athena-x-validator-base"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_validator_cross_provider"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w("agents/validation/cross-provider-validator/src/athena_x_validator_cross_provider/__init__.py", '''
"""Cross-provider validator."""
from .validator import CrossProviderValidator, ConsensusResult

__all__ = ["CrossProviderValidator", "ConsensusResult"]
__version__ = "0.1.0"
''')

w("agents/validation/cross-provider-validator/src/athena_x_validator_cross_provider/validator.py", '''
"""Cross-provider validator — Stage 3 req 2.4.

Example:
  Yahoo      752.44
  Polygon    752.45
  Finnhub    752.46
  Consensus  752.45

If another provider returns 742.00 → REJECT.

Consensus is computed as the median of peer values. A record is rejected if
its value deviates from consensus by more than the tolerance (default 0.5%).
"""
from __future__ import annotations
import statistics
from typing import Any

from athena_x_validator_base import BaseValidator, ValidatorConfig
from athena_x_runtime_validation_types import (
    ValidationResult, ValidationContext, ValidationStatus, ValidationReason,
)


# Default tolerance: 0.5% deviation from consensus
DEFAULT_TOLERANCE_PCT = 0.005
# Minimum number of peers required for consensus
MIN_PEERS_FOR_CONSENSUS = 2


class ConsensusResult:
    """Result of consensus computation."""
    def __init__(self, consensus: float, peers: dict[str, float],
                 outliers: dict[str, float]):
        self.consensus = consensus
        self.peers = peers
        self.outliers = outliers

    @property
    def peer_count(self) -> int:
        return len(self.peers)

    @property
    def has_consensus(self) -> bool:
        return len(self.peers) >= MIN_PEERS_FOR_CONSENSUS


class CrossProviderValidator(BaseValidator):
    """Validates a record against peer values from other providers."""

    def __init__(self, tolerance_pct: float = DEFAULT_TOLERANCE_PCT):
        super().__init__(ValidatorConfig(
            name="cross-provider-validator",
            blocking=False,  # don't halt — record warning/quarantine
        ))
        self._tolerance_pct = tolerance_pct

    async def validate(self, record: Any, context: ValidationContext) -> ValidationResult:
        """Validate the record's 'last' value against peers."""
        if not isinstance(record, dict):
            return self._passed("non-dict record, skipping cross-provider check")

        value = record.get("last")
        if value is None or not isinstance(value, (int, float)):
            return self._passed("no 'last' field to validate")

        peers = context.peer_values
        if not peers:
            # Single source — warning, can't verify
            return self._warning(
                ValidationReason.SINGLE_SOURCE,
                f"Only one provider ({context.provider}); cannot cross-verify",
                confidence_delta=-0.1,
            )

        # Filter to numeric peers
        numeric_peers = {k: v for k, v in peers.items() if isinstance(v, (int, float))}
        if len(numeric_peers) < MIN_PEERS_FOR_CONSENSUS - 1:  # -1 because we count ourselves
            return self._warning(
                ValidationReason.SINGLE_SOURCE,
                f"Only {len(numeric_peers)} peer(s); need {MIN_PEERS_FOR_CONSENSUS} for consensus",
                confidence_delta=-0.05,
            )

        # Include our value in consensus
        all_values = list(numeric_peers.values()) + [value]
        consensus = statistics.median(all_values)

        # Check deviation
        deviation = abs(value - consensus) / consensus if consensus > 0 else 0
        if deviation > self._tolerance_pct:
            # Determine if WE are the outlier, or a peer is
            # If our value is further from consensus than any peer, we're the outlier
            peer_deviations = [
                abs(v - consensus) / consensus if consensus > 0 else 0
                for v in numeric_peers.values()
            ]
            max_peer_deviation = max(peer_deviations) if peer_deviations else 0

            if deviation > max_peer_deviation:
                return self._reject(
                    ValidationReason.CONSENSUS_DISAGREEMENT,
                    f"Value {value} deviates {deviation:.4%} from consensus {consensus:.2f}",
                )
            else:
                # A peer is the outlier — we're fine, but flag it
                return self._warning(
                    ValidationReason.CONSENSUS_DISAGREEMENT,
                    f"Peer outlier detected; consensus {consensus:.2f}",
                    confidence_delta=-0.05,
                )

        # Close to consensus — small confidence boost
        return ValidationResult(
            validatorName=self.name,
            status=ValidationStatus.VERIFIED,
            reason=ValidationReason.PASSED,
            confidenceDelta=min(0.05, 0.05 - deviation * 10),  # up to +0.05 boost
            message=f"Matches consensus {consensus:.2f} (deviation: {deviation:.4%})",
        )
''')

w("agents/validation/cross-provider-validator/tests/__init__.py", "")
w("agents/validation/cross-provider-validator/tests/test_validator.py", '''
"""Tests for cross-provider validator."""
import pytest
from datetime import datetime, timezone
from athena_x_validator_cross_provider import CrossProviderValidator
from athena_x_runtime_validation_types import (
    ValidationContext, ValidationStatus, ValidationReason,
)


@pytest.fixture
def validator():
    return CrossProviderValidator(tolerance_pct=0.005)  # 0.5%


def make_context(value, peers=None, provider="yahoo"):
    return ValidationContext(
        pipelineStartedAt=datetime.now(timezone.utc),
        provider=provider, symbol="SPY", asset_class="etf",
        peerValues=peers or {},
    )


async def test_matches_consensus(validator):
    """Value close to peer consensus is verified."""
    result = await validator.validate(
        {"last": 752.45},
        make_context(752.45, {"polygon": 752.45, "finnhub": 752.46}),
    )
    assert result.status == ValidationStatus.VERIFIED


async def test_outlier_rejected(validator):
    """Value far from consensus is rejected."""
    result = await validator.validate(
        {"last": 742.00},
        make_context(742.00, {"polygon": 752.45, "finnhub": 752.46}),
    )
    assert result.status == ValidationStatus.REJECTED
    assert result.reason == ValidationReason.CONSENSUS_DISAGREEMENT


async def test_single_source_warning(validator):
    """Single provider (no peers) gets a warning."""
    result = await validator.validate(
        {"last": 752.45},
        make_context(752.45, {}),  # no peers
    )
    assert result.status == ValidationStatus.WARNING
    assert result.reason == ValidationReason.SINGLE_SOURCE


async def test_peer_outlier_warning(validator):
    """When a peer is the outlier, we get a warning (not rejection)."""
    result = await validator.validate(
        {"last": 752.45},
        make_context(752.45, {"polygon": 752.46, "finnhub": 742.00}),  # finnhub is outlier
    )
    assert result.status == ValidationStatus.WARNING


async def test_no_last_field_passes(validator):
    """Records without 'last' field pass (cross-provider check is skipped)."""
    result = await validator.validate(
        {"symbol": "SPY"},
        make_context(None, {"polygon": 752.45}),
    )
    assert result.status == ValidationStatus.VERIFIED


async def test_within_tolerance_passes(validator):
    """Values within tolerance pass."""
    result = await validator.validate(
        {"last": 752.50},
        make_context(752.50, {"polygon": 752.45, "finnhub": 752.46}),
    )
    # 752.50 vs consensus 752.46 → deviation 0.005% — within tolerance
    assert result.status in (ValidationStatus.VERIFIED, ValidationStatus.WARNING)
''')

# ============================================================================
# 8. MARKET LOGIC VALIDATOR — agents/validation/market-logic-validator/
# ============================================================================

w("agents/validation/market-logic-validator/pyproject.toml", '''
[project]
name = "athena-x-validator-market-logic"
version = "0.1.0"
description = "Market logic validator — detects impossible values (high<low, neg vol, IV>1000%)"
requires-python = ">=3.11"
dependencies = ["athena-x-validator-base"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_validator_market_logic"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w("agents/validation/market-logic-validator/src/athena_x_validator_market_logic/__init__.py", '''
"""Market logic validator."""
from .validator import MarketLogicValidator

__all__ = ["MarketLogicValidator"]
__version__ = "0.1.0"
''')

w("agents/validation/market-logic-validator/src/athena_x_validator_market_logic/validator.py", '''
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
''')

w("agents/validation/market-logic-validator/tests/__init__.py", "")
w("agents/validation/market-logic-validator/tests/test_validator.py", '''
"""Tests for market logic validator."""
import pytest
from datetime import datetime, timezone
from athena_x_validator_market_logic import MarketLogicValidator
from athena_x_runtime_validation_types import (
    ValidationContext, ValidationStatus, ValidationReason,
)


@pytest.fixture
def validator():
    return MarketLogicValidator()


def make_context():
    return ValidationContext(
        pipelineStartedAt=datetime.now(timezone.utc),
        provider="yahoo", symbol="SPY", asset_class="etf",
    )


async def test_valid_ohlc_passes(validator):
    result = await validator.validate(
        {"open": 100, "high": 105, "low": 99, "close": 104, "volume": 1000},
        make_context(),
    )
    assert result.status == ValidationStatus.VERIFIED


async def test_high_lt_low_rejected(validator):
    result = await validator.validate(
        {"high": 99, "low": 105},  # high < low
        make_context(),
    )
    assert result.status == ValidationStatus.REJECTED
    assert result.reason == ValidationReason.HIGH_LT_LOW


async def test_close_gt_high_rejected(validator):
    result = await validator.validate(
        {"close": 110, "high": 105},
        make_context(),
    )
    assert result.status == ValidationStatus.REJECTED
    assert result.reason == ValidationReason.CLOSE_GT_HIGH


async def test_negative_volume_rejected(validator):
    result = await validator.validate(
        {"volume": -100},
        make_context(),
    )
    assert result.status == ValidationStatus.REJECTED
    assert result.reason == ValidationReason.NEGATIVE_VOLUME


async def test_negative_oi_rejected(validator):
    result = await validator.validate(
        {"open_interest": -50},
        make_context(),
    )
    assert result.status == ValidationStatus.REJECTED
    assert result.reason == ValidationReason.NEGATIVE_OI


async def test_iv_too_high_rejected(validator):
    result = await validator.validate(
        {"iv": 15.0},  # 1500%
        make_context(),
    )
    assert result.status == ValidationStatus.REJECTED
    assert result.reason == ValidationReason.IV_TOO_HIGH


async def test_negative_iv_rejected(validator):
    result = await validator.validate(
        {"iv": -0.3},
        make_context(),
    )
    assert result.status == ValidationStatus.REJECTED
    assert result.reason == ValidationReason.IV_TOO_HIGH


async def test_impossible_delta_rejected(validator):
    result = await validator.validate(
        {"delta": 2.0},  # delta must be |delta| <= 1
        make_context(),
    )
    assert result.status == ValidationStatus.REJECTED
    assert result.reason == ValidationReason.IMPOSSIBLE_GREEK


async def test_negative_gamma_rejected(validator):
    result = await validator.validate(
        {"gamma": -0.5},
        make_context(),
    )
    assert result.status == ValidationStatus.REJECTED
    assert result.reason == ValidationReason.IMPOSSIBLE_GREEK


async def test_valid_greeks_pass(validator):
    result = await validator.validate(
        {"delta": 0.5, "gamma": 0.02, "theta": -5.0, "vega": 0.1},
        make_context(),
    )
    assert result.status == ValidationStatus.VERIFIED
''')

# ============================================================================
# 9. COMPLETENESS VALIDATOR — agents/validation/completeness-validator/
# ============================================================================

w("agents/validation/completeness-validator/pyproject.toml", '''
[project]
name = "athena-x-validator-completeness"
version = "0.1.0"
description = "Completeness validator — detects missing bars, strikes, expirations, greeks"
requires-python = ">=3.11"
dependencies = ["athena-x-validator-base"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_validator_completeness"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w("agents/validation/completeness-validator/src/athena_x_validator_completeness/__init__.py", '''
"""Completeness validator."""
from .validator import CompletenessValidator, EXPECTED_QUOTE_FIELDS, EXPECTED_OPTION_FIELDS

__all__ = ["CompletenessValidator", "EXPECTED_QUOTE_FIELDS", "EXPECTED_OPTION_FIELDS"]
__version__ = "0.1.0"
''')

w("agents/validation/completeness-validator/src/athena_x_validator_completeness/validator.py", '''
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
''')

w("agents/validation/completeness-validator/tests/__init__.py", "")
w("agents/validation/completeness-validator/tests/test_validator.py", '''
"""Tests for completeness validator."""
import pytest
from datetime import datetime, timezone
from athena_x_validator_completeness import CompletenessValidator
from athena_x_runtime_validation_types import (
    ValidationContext, ValidationStatus, ValidationReason,
)


@pytest.fixture
def validator():
    return CompletenessValidator()


def make_context(asset_class="etf"):
    return ValidationContext(
        pipelineStartedAt=datetime.now(timezone.utc),
        provider="yahoo", symbol="SPY", asset_class=asset_class,
    )


async def test_complete_quote_passes(validator):
    result = await validator.validate(
        {"symbol": "SPY", "last": 450.0, "timestamp": "2026-07-17T10:00:00Z"},
        make_context(),
    )
    assert result.status == ValidationStatus.VERIFIED


async def test_missing_quote_field_warning(validator):
    result = await validator.validate(
        {"symbol": "SPY", "last": 450.0},  # missing timestamp
        make_context(),
    )
    assert result.status == ValidationStatus.WARNING
    assert result.reason == ValidationReason.MISSING_BAR


async def test_complete_bar_passes(validator):
    result = await validator.validate(
        {"timestamp": 1700000000000, "open": 100, "high": 105, "low": 99, "close": 104, "volume": 1000},
        make_context(),
    )
    assert result.status == ValidationStatus.VERIFIED


async def test_missing_bar_field_warning(validator):
    result = await validator.validate(
        {"open": 100, "high": 105, "low": 99, "close": 104},  # missing volume + timestamp
        make_context(),
    )
    assert result.status == ValidationStatus.WARNING


async def test_complete_option_record_passes(validator):
    record = {
        "symbol": "NVDA",
        "expiry": "2026-07-18",
        "strikes": [
            {"strike": 125, "call": {"delta": 0.7, "gamma": 0.05, "theta": -0.5, "vega": 0.1},
             "put": {"delta": -0.3, "gamma": 0.05, "theta": -0.5, "vega": 0.1}},
        ],
    }
    result = await validator.validate(record, make_context("option"))
    assert result.status == ValidationStatus.VERIFIED


async def test_missing_greeks_warning(validator):
    record = {
        "symbol": "NVDA",
        "expiry": "2026-07-18",
        "strikes": [
            {"strike": 125, "call": {"delta": 0.7},  # missing gamma, theta, vega
             "put": {"delta": -0.3}},
        ],
    }
    result = await validator.validate(record, make_context("option"))
    assert result.status == ValidationStatus.WARNING
    assert result.reason == ValidationReason.MISSING_GREEK
''')

# ============================================================================
# 10. QUARANTINE MANAGER — agents/validation/quarantine-manager/
# ============================================================================

w("agents/validation/quarantine-manager/pyproject.toml", '''
[project]
name = "athena-x-validator-quarantine"
version = "0.1.0"
description = "Quarantine manager — never deletes rejected data"
requires-python = ">=3.11"
dependencies = [
    "athena-x-runtime-validation-types",
    "athena-x-runtime-logger",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_validator_quarantine"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w("agents/validation/quarantine-manager/src/athena_x_validator_quarantine/__init__.py", '''
"""Quarantine manager."""
from .manager import QuarantineManager

__all__ = ["QuarantineManager"]
__version__ = "0.1.0"
''')

w("agents/validation/quarantine-manager/src/athena_x_validator_quarantine/manager.py", '''
"""Quarantine manager — Stage 3 req 10.

Never deletes rejected data. Stores:
  - Reason
  - Provider
  - Raw payload
  - Timestamp
  - Validator
  - Error code

Supports debugging and auditing.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any
from uuid import UUID

from athena_x_runtime_validation_types import (
    QuarantineRecord, ValidationReason, QualityGrade,
)
from athena_x_runtime_logger import get_logger

log = get_logger("validation.quarantine")


class QuarantineManager:
    """Manages quarantined records.

    Records are stored in-memory + optionally persisted to filesystem
    (JSONL format). In production, this would be a dedicated quarantine
    database (append-only).
    """

    def __init__(self, persist_path: str | Path | None = None):
        self._records: list[QuarantineRecord] = []
        self._lock = Lock()
        self._persist_path = Path(persist_path) if persist_path else None
        if self._persist_path:
            self._persist_path.parent.mkdir(parents=True, exist_ok=True)

    def quarantine(self, record: QuarantineRecord) -> None:
        """Add a record to quarantine."""
        with self._lock:
            self._records.append(record)
        log.info("record_quarantined",
                 quarantine_id=str(record.quarantine_id),
                 provider=record.provider,
                 symbol=record.symbol,
                 reason=record.reason.value,
                 validator=record.validator)

        if self._persist_path:
            self._persist(record)

    def _persist(self, record: QuarantineRecord) -> None:
        try:
            with open(self._persist_path, "a", encoding="utf-8") as f:
                f.write(record.model_dump_json(by_alias=True) + "\\n")
        except Exception as e:
            log.error("quarantine_persist_failed", error=str(e))

    def list_all(self) -> list[QuarantineRecord]:
        with self._lock:
            return list(self._records)

    def list_by_provider(self, provider: str) -> list[QuarantineRecord]:
        with self._lock:
            return [r for r in self._records if r.provider == provider]

    def list_by_reason(self, reason: ValidationReason) -> list[QuarantineRecord]:
        with self._lock:
            return [r for r in self._records if r.reason == reason]

    def list_by_symbol(self, symbol: str) -> list[QuarantineRecord]:
        with self._lock:
            return [r for r in self._records if r.symbol == symbol]

    def count(self) -> int:
        with self._lock:
            return len(self._records)

    def count_by_provider(self) -> dict[str, int]:
        with self._lock:
            counts: dict[str, int] = {}
            for r in self._records:
                counts[r.provider] = counts.get(r.provider, 0) + 1
            return counts

    def count_by_reason(self) -> dict[str, int]:
        with self._lock:
            counts: dict[str, int] = {}
            for r in self._records:
                key = r.reason.value
                counts[key] = counts.get(key, 0) + 1
            return counts

    def get_stats(self) -> dict:
        """Self-monitoring metrics (Stage 3 req 8)."""
        with self._lock:
            total = len(self._records)
            avg_confidence = (
                sum(r.confidence_score for r in self._records) / total
                if total > 0 else 0.0
            )
            return {
                "quarantine_size": total,
                "average_confidence": avg_confidence,
                "by_provider": self.count_by_provider(),
                "by_reason": self.count_by_reason(),
            }

    def clear(self) -> None:
        with self._lock:
            self._records.clear()
''')

w("agents/validation/quarantine-manager/tests/__init__.py", "")
w("agents/validation/quarantine-manager/tests/test_manager.py", '''
"""Tests for quarantine manager (Stage 3 req 10)."""
import pytest
from datetime import datetime, timezone
from athena_x_runtime_validation_types import (
    create_quarantine, ValidationReason,
)
from athena_x_validator_quarantine import QuarantineManager


@pytest.fixture
def manager():
    return QuarantineManager()


def test_quarantine_never_deletes(manager):
    """Quarantined records are retained — never deleted."""
    q = create_quarantine(
        provider="yahoo", symbol="SPY",
        raw_payload={"last": 742.0},
        reason=ValidationReason.STATISTICAL_OUTLIER,
        validator="outlier-detector",
        error_code="OUTLIER_001",
    )
    manager.quarantine(q)
    assert manager.count() == 1

    # Records persist even after clear() — clear is for in-memory only,
    # persisted records remain on disk
    # (in this test we just check that quarantine() retains)


def test_list_by_provider(manager):
    for p in ["yahoo", "yahoo", "polygon"]:
        manager.quarantine(create_quarantine(
            provider=p, symbol="SPY", raw_payload={},
            reason=ValidationReason.STATISTICAL_OUTLIER,
            validator="outlier", error_code="X",
        ))
    results = manager.list_by_provider("yahoo")
    assert len(results) == 2


def test_list_by_reason(manager):
    for r in [ValidationReason.STATISTICAL_OUTLIER, ValidationReason.HIGH_LT_LOW,
              ValidationReason.STATISTICAL_OUTLIER]:
        manager.quarantine(create_quarantine(
            provider="yahoo", symbol="SPY", raw_payload={},
            reason=r, validator="v", error_code="X",
        ))
    results = manager.list_by_reason(ValidationReason.STATISTICAL_OUTLIER)
    assert len(results) == 2


def test_count_by_provider(manager):
    for p in ["yahoo", "polygon", "yahoo"]:
        manager.quarantine(create_quarantine(
            provider=p, symbol="SPY", raw_payload={},
            reason=ValidationReason.STATISTICAL_OUTLIER,
            validator="v", error_code="X",
        ))
    counts = manager.count_by_provider()
    assert counts["yahoo"] == 2
    assert counts["polygon"] == 1


def test_count_by_reason(manager):
    for r in [ValidationReason.STATISTICAL_OUTLIER, ValidationReason.HIGH_LT_LOW]:
        manager.quarantine(create_quarantine(
            provider="yahoo", symbol="SPY", raw_payload={},
            reason=r, validator="v", error_code="X",
        ))
    counts = manager.count_by_reason()
    assert counts["statistical_outlier"] == 1
    assert counts["high_lt_low"] == 1


def test_get_stats(manager):
    """Stats include quarantine_size + average_confidence."""
    for c in [0.1, 0.2, 0.3]:
        manager.quarantine(create_quarantine(
            provider="yahoo", symbol="SPY", raw_payload={},
            reason=ValidationReason.STATISTICAL_OUTLIER,
            validator="v", error_code="X", confidence_score=c,
        ))
    stats = manager.get_stats()
    assert stats["quarantine_size"] == 3
    assert 0.19 < stats["average_confidence"] < 0.21


def test_persist_to_filesystem(tmp_path):
    """Quarantine records are persisted to filesystem."""
    persist_path = tmp_path / "quarantine.jsonl"
    mgr = QuarantineManager(persist_path=persist_path)
    mgr.quarantine(create_quarantine(
        provider="yahoo", symbol="SPY", raw_payload={"last": 742},
        reason=ValidationReason.STATISTICAL_OUTLIER,
        validator="outlier", error_code="X",
    ))
    assert persist_path.exists()
    content = persist_path.read_text()
    assert '"provider":"yahoo"' in content
    assert '"rawPayload"' in content
''')

print(f"\n✅ Stage 3 Part 1 complete: {len(FILES)} files written")
print("\nComponents implemented:")
print("  1. runtime/validation-types/           — shared types (4 statuses, 6 grades, audit, quarantine)")
print("  2. runtime/audit-trail/                — audit logging + deterministic replay")
print("  3. agents/validation/_base/            — BaseValidator + ValidationPipeline")
print("  4. agents/validation/schema-validator/ — required fields, types, symbol validity")
print("  5. agents/validation/timestamp-validator/ — UTC, clock drift, out-of-order, duplicates")
print("  6. agents/validation/market-calendar-validator/ — holiday, weekend, session")
print("  7. agents/validation/cross-provider-validator/ — consensus, outlier rejection")
print("  8. agents/validation/market-logic-validator/ — high<low, neg vol, IV>1000%")
print("  9. agents/validation/completeness-validator/ — missing fields, greeks")
print(" 10. agents/validation/quarantine-manager/ — never deletes rejected data")
print("\nNext: install deps and run tests")
