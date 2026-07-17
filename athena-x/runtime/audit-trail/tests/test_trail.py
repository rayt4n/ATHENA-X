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
