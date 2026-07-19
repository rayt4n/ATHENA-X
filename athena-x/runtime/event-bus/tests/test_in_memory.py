"""Tests for InMemoryBusClient."""
import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from athena_x_runtime_event_bus import BusEvent, InMemoryBusClient


@pytest.fixture
async def bus():
    b = InMemoryBusClient(backpressure_max_age_ms=500)
    yield b
    await b.close()


async def test_publish_subscribe_basic(bus):
    """A published event reaches a subscribed handler."""
    received = []

    async def handler(event):
        received.append(event)

    await bus.subscribe("market:*", handler)

    event = BusEvent.create(
        event_type="market:quote-updated",
        provider="yahoo",
        agent_id="data-collection.collection",
        payload={"symbol": "NVDA"},
    )
    await bus.publish(event)

    assert len(received) == 1
    assert received[0].event_id == event.event_id


async def test_pattern_matching_glob(bus):
    """'*' matches all events."""
    received = []

    async def handler(event):
        received.append(event)

    await bus.subscribe("*", handler)

    for et in ["market:quote-updated", "ta:signal-emitted", "news:headline-received"]:
        await bus.publish(BusEvent.create(
            event_type=et, provider="test", agent_id="test", payload={}
        ))

    assert len(received) == 3


async def test_pattern_matching_prefix(bus):
    """'market:*' matches only market events."""
    market_events = []
    ta_events = []

    async def market_handler(event):
        market_events.append(event)

    async def ta_handler(event):
        ta_events.append(event)

    await bus.subscribe("market:*", market_handler)
    await bus.subscribe("ta:*", ta_handler)

    await bus.publish(BusEvent.create(
        event_type="market:quote-updated", provider="test", agent_id="test", payload={}
    ))
    await bus.publish(BusEvent.create(
        event_type="ta:signal-emitted", provider="test", agent_id="test", payload={}
    ))

    assert len(market_events) == 1
    assert len(ta_events) == 1


async def test_unsubscribe(bus):
    """Unsubscribed handlers stop receiving events."""
    received = []

    async def handler(event):
        received.append(event)

    await bus.subscribe("market:*", handler)
    await bus.unsubscribe("market:*", handler)

    await bus.publish(BusEvent.create(
        event_type="market:quote-updated", provider="test", agent_id="test", payload={}
    ))

    assert len(received) == 0


async def test_backpressure_drops_stale_market_events(bus):
    """Market events older than 500ms are dropped (Change 11)."""
    received = []

    async def handler(event):
        received.append(event)

    await bus.subscribe("market:*", handler)

    # Publish a stale event (1 second old)
    stale_event = BusEvent.create(
        event_type="market:quote-updated",
        provider="yahoo",
        agent_id="test",
        payload={},
        timestamp=datetime.now(timezone.utc) - timedelta(seconds=1),
    )
    await bus.publish(stale_event)

    # Should have been dropped
    assert len(received) == 0
    assert bus.drop_count == 1


async def test_backpressure_keeps_fresh_events(bus):
    """Fresh market events are not dropped."""
    received = []

    async def handler(event):
        received.append(event)

    await bus.subscribe("market:*", handler)

    fresh_event = BusEvent.create(
        event_type="market:quote-updated",
        provider="yahoo",
        agent_id="test",
        payload={},
    )
    await bus.publish(fresh_event)

    assert len(received) == 1
    assert bus.drop_count == 0


async def test_backpressure_does_not_affect_non_market_events(bus):
    """TA, news, etc. events are never dropped due to backpressure."""
    received = []

    async def handler(event):
        received.append(event)

    await bus.subscribe("ta:*", handler)

    stale_event = BusEvent.create(
        event_type="ta:signal-emitted",
        provider="test",
        agent_id="test",
        payload={},
        timestamp=datetime.now(timezone.utc) - timedelta(seconds=10),
    )
    await bus.publish(stale_event)

    assert len(received) == 1


async def test_health_check(bus):
    """Health check returns True when open, False when closed."""
    assert await bus.health_check() is True
    await bus.close()
    assert await bus.health_check() is False


async def test_multiple_handlers_same_pattern(bus):
    """Multiple handlers on the same pattern all receive events."""
    received_a = []
    received_b = []

    async def handler_a(event):
        received_a.append(event)

    async def handler_b(event):
        received_b.append(event)

    await bus.subscribe("market:*", handler_a)
    await bus.subscribe("market:*", handler_b)

    await bus.publish(BusEvent.create(
        event_type="market:quote-updated", provider="test", agent_id="test", payload={}
    ))

    assert len(received_a) == 1
    assert len(received_b) == 1


async def test_publish_count_tracking(bus):
    """Bus tracks total publish count."""
    async def handler(event): pass
    await bus.subscribe("*", handler)

    for i in range(100):
        await bus.publish(BusEvent.create(
            event_type="market:quote-updated",
            provider="test", agent_id="test", payload={}
        ))

    assert bus.publish_count == 100
