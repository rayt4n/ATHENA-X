"""Tests for WebSocket bridge (Stage 6 req 9)."""
import pytest
from athena_x_runtime_event_envelope import create_event, EventPriority
from athena_x_runtime_websocket_bridge import WebSocketBridge


@pytest.fixture
def bridge():
    return WebSocketBridge()


def test_add_client(bridge):
    """Clients can be added."""
    client = bridge.add_client("client-1")
    assert client.client_id == "client-1"
    assert client.connected is True


def test_remove_client(bridge):
    """Clients can be removed."""
    bridge.add_client("client-1")
    bridge.remove_client("client-1")
    stats = bridge.get_stats()
    assert stats["connected_clients"] == 0


def test_subscribe_to_patterns(bridge):
    """Clients can subscribe to event patterns."""
    client = bridge.add_client("client-1")
    bridge.subscribe("client-1", ["market:*", "ai:forecast"])
    assert "market:*" in client.subscriptions
    assert "ai:forecast" in client.subscriptions


async def test_broadcast_delivers_to_subscribed_clients(bridge):
    """Broadcast delivers events to subscribed clients."""
    client = bridge.add_client("client-1")
    bridge.subscribe("client-1", ["market:*"])

    event = create_event(event_type="market:raw", source_agent="yahoo")
    delivered = await bridge.broadcast(event)

    assert delivered == 1
    received = await client.receive(timeout=0.1)
    assert received is not None
    assert received.event_type == "market:raw"


async def test_broadcast_skips_unsubscribed_events(bridge):
    """Broadcast doesn't deliver events that don't match subscription."""
    client = bridge.add_client("client-1")
    bridge.subscribe("client-1", ["market:*"])

    # Non-matching event
    event = create_event(event_type="ai:forecast", source_agent="lstm")
    delivered = await bridge.broadcast(event)

    assert delivered == 0
    received = await client.receive(timeout=0.1)
    assert received is None


async def test_broadcast_delivers_to_all_if_no_subscriptions(bridge):
    """Clients without subscriptions receive all events."""
    client = bridge.add_client("client-1")
    # No subscriptions set

    event = create_event(event_type="market:raw", source_agent="yahoo")
    delivered = await bridge.broadcast(event)
    assert delivered == 1


async def test_broadcast_to_multiple_clients(bridge):
    """Broadcast delivers to multiple clients."""
    c1 = bridge.add_client("client-1")
    c2 = bridge.add_client("client-2")
    c3 = bridge.add_client("client-3")

    event = create_event(event_type="market:raw", source_agent="yahoo")
    delivered = await bridge.broadcast(event)
    assert delivered == 3


async def test_drop_when_client_queue_full(bridge):
    """Events are dropped when client queue is full."""
    client = bridge.add_client("client-1")
    # Fill the queue (maxsize=1000)
    for i in range(1000):
        await client.send(create_event(event_type="t", source_agent="t"))

    # Next send should drop oldest for high priority
    event = create_event(event_type="market:raw", source_agent="t", priority=EventPriority.HIGH)
    result = await client.send(event)
    assert result is True  # accepted (dropped oldest)
    assert client.events_dropped > 0


def test_get_stats(bridge):
    """get_stats returns bridge statistics."""
    bridge.add_client("client-1")
    bridge.add_client("client-2")
    stats = bridge.get_stats()
    assert stats["connected_clients"] == 2
    assert "clients" in stats
