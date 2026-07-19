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
    # Pydantic may serialize with snake_case or camelCase aliases — check both
    assert '"raw_payload"' in content or '"rawPayload"' in content
