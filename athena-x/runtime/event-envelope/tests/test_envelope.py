"""Tests for standard event envelope (Stage 6 req 2)."""
import pytest
from datetime import datetime, timezone
from uuid import uuid4
from athena_x_runtime_event_envelope import (
    EventEnvelope, EventPriority, EventCategory,
    create_event, ENVELOPE_SCHEMA_VERSION,
    EVENT_CATEGORIES, list_event_types,
)


def test_envelope_has_10_mandatory_fields():
    """Every event has 10 mandatory fields."""
    e = create_event(
        event_type="market:raw",
        source_agent="data-collection.yahoo",
        payload={"symbol": "SPY", "last": 450.0},
    )
    assert e.event_id is not None
    assert e.event_type == "market:raw"
    assert e.source_agent == "data-collection.yahoo"
    assert e.correlation_id is not None
    assert e.timestamp.tzinfo is not None
    assert e.schema_version == ENVELOPE_SCHEMA_VERSION
    assert e.priority == EventPriority.NORMAL
    assert e.processing_time_ms == 0
    assert e.payload == {"symbol": "SPY", "last": 450.0}


def test_priority_levels():
    """4 priority levels exist."""
    assert EventPriority.CRITICAL.value == "critical"
    assert EventPriority.HIGH.value == "high"
    assert EventPriority.NORMAL.value == "normal"
    assert EventPriority.LOW.value == "low"


def test_category_extracted_from_event_type():
    """Category is extracted from event_type prefix."""
    e = create_event(event_type="market:raw", source_agent="test")
    assert e.category == EventCategory.MARKET

    e2 = create_event(event_type="ai:forecast", source_agent="test")
    assert e2.category == EventCategory.AI


def test_correlation_id_propagation():
    """with_correlation creates a child event with shared correlation ID."""
    parent = create_event(event_type="market:raw", source_agent="yahoo")
    child = parent.with_correlation(parent.correlation_id)
    assert child.correlation_id == parent.correlation_id
    assert child.event_id != parent.event_id  # different event ID


def test_create_event_auto_generates_ids():
    """create_event auto-generates event_id and correlation_id."""
    e = create_event(event_type="market:raw", source_agent="test")
    assert e.event_id is not None
    assert e.correlation_id is not None


def test_naive_timestamp_rejected():
    """Timestamps must be UTC-aware."""
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        EventEnvelope(
            event_id=uuid4(),
            event_type="test",
            source_agent="test",
            correlation_id=uuid4(),
            timestamp=datetime.now(),  # naive!
        )


def test_serialization_roundtrip():
    """Envelope serializes to JSON and back."""
    e = create_event(
        event_type="market:raw",
        source_agent="yahoo",
        symbol="SPY",
        priority=EventPriority.HIGH,
        payload={"last": 450.0},
    )
    json_str = e.model_dump_json()
    restored = EventEnvelope.model_validate_json(json_str)
    assert restored.event_type == "market:raw"
    assert restored.priority == EventPriority.HIGH
    assert restored.symbol == "SPY"


def test_5_event_categories_defined():
    """All 5 (actually 6) event categories are defined."""
    assert "market" in EVENT_CATEGORIES
    assert "options" in EVENT_CATEGORIES
    assert "news" in EVENT_CATEGORIES
    assert "ai" in EVENT_CATEGORIES
    assert "reports" in EVENT_CATEGORIES
    assert "system" in EVENT_CATEGORIES


def test_list_event_types():
    """list_event_types returns all or filtered."""
    all_types = list_event_types()
    assert "market:raw" in all_types
    assert "ai:forecast" in all_types

    market_only = list_event_types("market")
    assert "market:raw" in market_only
    assert "ai:forecast" not in market_only


def test_priority_used_in_create_event():
    """create_event accepts priority parameter."""
    e = create_event(
        event_type="system:error",
        source_agent="test",
        priority=EventPriority.CRITICAL,
    )
    assert e.priority == EventPriority.CRITICAL
