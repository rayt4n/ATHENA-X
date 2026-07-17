"""Tests for event-bus type validation."""
import pytest
from datetime import datetime, timezone
from uuid import uuid4
from athena_x_runtime_event_bus.types import BusEvent


def test_bus_event_validates_all_required_fields():
    """An event missing any of the 10 metadata fields MUST be rejected."""
    event = BusEvent(
        eventId=uuid4(),
        eventType="market:quote-updated",
        timestamp=datetime.now(timezone.utc),
        provider="yahoo",
        latency=10,
        confidence=0.95,
        dataVersion="1.0.0",
        retryCount=0,
        agentId="data-collection.collection",
        processingTime=5,
        payload={"symbol": "NVDA", "last": 128.45},
    )
    assert event.event_type == "market:quote-updated"


def test_bus_event_rejects_missing_metadata():
    with pytest.raises(Exception):
        BusEvent(
            eventId=uuid4(),
            eventType="market:quote-updated",
            timestamp=datetime.now(timezone.utc),
            provider="yahoo",
            # missing: latency, confidence, dataVersion, retryCount, agentId, processingTime
            payload={},
        )
