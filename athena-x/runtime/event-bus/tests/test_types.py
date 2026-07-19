"""Tests for event bus type validation (Change 11 — 10 mandatory fields)."""
import pytest
from datetime import datetime, timezone
from uuid import uuid4
from athena_x_runtime_event_bus import BusEvent


def test_event_factory_creates_valid_event():
    """create() factory fills all 10 mandatory fields."""
    event = BusEvent.create(
        event_type="market:quote-updated",
        provider="yahoo",
        agent_id="data-collection.collection",
        payload={"symbol": "NVDA", "last": 128.45},
    )
    assert event.event_id is not None
    assert event.event_type == "market:quote-updated"
    assert event.timestamp.tzinfo is not None
    assert event.provider == "yahoo"
    assert event.latency == 0
    assert event.confidence == 1.0
    assert event.data_version == "1.0.0"
    assert event.retry_count == 0
    assert event.agent_id == "data-collection.collection"
    assert event.processing_time == 0
    assert event.payload == {"symbol": "NVDA", "last": 128.45}


def test_event_rejects_missing_metadata():
    """An event missing any of the 10 mandatory fields MUST be rejected."""
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        BusEvent(
            eventId=uuid4(),
            eventType="market:quote-updated",
            timestamp=datetime.now(timezone.utc),
            provider="yahoo",
            # missing: latency, confidence, dataVersion, retryCount, agentId, processingTime
            payload={},
        )


def test_event_rejects_naive_timestamp():
    """Timestamp must be UTC timezone-aware."""
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        BusEvent(
            eventId=uuid4(),
            eventType="test",
            timestamp=datetime.now(),  # naive!
            provider="test",
            latency=0,
            confidence=1.0,
            data_version="1.0.0",
            retry_count=0,
            agent_id="test",
            processing_time=0,
            payload={},
        )


def test_event_rejects_invalid_confidence():
    """Confidence must be 0..1."""
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        BusEvent.create(
            event_type="test",
            provider="test",
            agent_id="test",
            payload={},
            confidence=1.5,
        )


def test_event_rejects_invalid_data_version():
    """data_version must be semver."""
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        BusEvent.create(
            event_type="test",
            provider="test",
            agent_id="test",
            payload={},
            data_version="invalid",
        )


def test_event_serializes_to_json():
    """Event serializes to JSON with camelCase aliases."""
    event = BusEvent.create(
        event_type="market:quote-updated",
        provider="yahoo",
        agent_id="data-collection.collection",
        payload={"symbol": "NVDA"},
    )
    json_str = event.model_dump_json(by_alias=True)
    assert '"eventId"' in json_str
    assert '"eventType"' in json_str
    assert '"dataVersion"' in json_str
    assert '"retryCount"' in json_str
    assert '"agentId"' in json_str
    assert '"processingTime"' in json_str


def test_event_deserializes_from_json():
    """Event round-trips through JSON."""
    original = BusEvent.create(
        event_type="market:quote-updated",
        provider="yahoo",
        agent_id="data-collection.collection",
        payload={"symbol": "NVDA", "last": 128.45},
        confidence=0.95,
        latency=10,
        processing_time=5,
    )
    json_str = original.model_dump_json(by_alias=True)
    restored = BusEvent.model_validate_json(json_str)
    assert restored.event_id == original.event_id
    assert restored.event_type == original.event_type
    assert restored.confidence == original.confidence
    assert restored.payload == original.payload
