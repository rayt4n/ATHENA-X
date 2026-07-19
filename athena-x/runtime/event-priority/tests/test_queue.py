"""Tests for priority queue (Stage 6 req 3)."""
import pytest
from athena_x_runtime_event_envelope import create_event, EventPriority
from athena_x_runtime_event_priority import PriorityQueue


async def test_dequeue_order_critical_first():
    """Critical events are dequeued first."""
    q = PriorityQueue()
    await q.enqueue(create_event(event_type="system:health", source_agent="t", priority=EventPriority.LOW))
    await q.enqueue(create_event(event_type="market:raw", source_agent="t", priority=EventPriority.NORMAL))
    await q.enqueue(create_event(event_type="system:error", source_agent="t", priority=EventPriority.CRITICAL))
    await q.enqueue(create_event(event_type="market:raw", source_agent="t", priority=EventPriority.HIGH))

    first = await q.dequeue(timeout=1.0)
    assert first.priority == EventPriority.CRITICAL
    second = await q.dequeue(timeout=1.0)
    assert second.priority == EventPriority.HIGH
    third = await q.dequeue(timeout=1.0)
    assert third.priority == EventPriority.NORMAL
    fourth = await q.dequeue(timeout=1.0)
    assert fourth.priority == EventPriority.LOW


async def test_fifo_within_priority():
    """Within the same priority, events are FIFO."""
    q = PriorityQueue()
    for i in range(5):
        await q.enqueue(create_event(
            event_type="market:raw", source_agent="t",
            priority=EventPriority.NORMAL, payload={"i": i},
        ))

    for expected in range(5):
        event = await q.dequeue(timeout=1.0)
        assert event.payload["i"] == expected


async def test_low_priority_dropped_when_full():
    """Low-priority events are dropped when queue is full."""
    q = PriorityQueue(max_size_per_level=2)
    # Fill low queue
    assert await q.enqueue(create_event(event_type="t", source_agent="t", priority=EventPriority.LOW))
    assert await q.enqueue(create_event(event_type="t", source_agent="t", priority=EventPriority.LOW))
    # Third should be dropped
    result = await q.enqueue(create_event(event_type="t", source_agent="t", priority=EventPriority.LOW))
    assert result is False

    stats = q.get_stats()
    assert stats.total_dropped == 1


async def test_critical_never_dropped():
    """Critical events are never dropped even when queue is full."""
    q = PriorityQueue(max_size_per_level=2)
    await q.enqueue(create_event(event_type="t", source_agent="t", priority=EventPriority.CRITICAL))
    await q.enqueue(create_event(event_type="t", source_agent="t", priority=EventPriority.CRITICAL))
    # Third critical should still be accepted
    result = await q.enqueue(create_event(event_type="t", source_agent="t", priority=EventPriority.CRITICAL))
    assert result is True


async def test_normal_drops_oldest():
    """Normal priority drops oldest to make room."""
    q = PriorityQueue(max_size_per_level=2)
    await q.enqueue(create_event(event_type="t", source_agent="t", priority=EventPriority.NORMAL, payload={"i": 1}))
    await q.enqueue(create_event(event_type="t", source_agent="t", priority=EventPriority.NORMAL, payload={"i": 2}))
    # Add third - should drop oldest
    await q.enqueue(create_event(event_type="t", source_agent="t", priority=EventPriority.NORMAL, payload={"i": 3}))

    first = await q.dequeue(timeout=1.0)
    assert first.payload["i"] == 2  # oldest (i=1) was dropped


async def test_queue_stats():
    """Queue tracks enqueue/dequeue/drop stats."""
    q = PriorityQueue()
    await q.enqueue(create_event(event_type="t", source_agent="t", priority=EventPriority.HIGH))
    await q.enqueue(create_event(event_type="t", source_agent="t", priority=EventPriority.NORMAL))
    await q.dequeue(timeout=1.0)

    stats = q.get_stats()
    assert stats.total_enqueued == 2
    assert stats.total_dequeued == 1
    assert stats.total_pending == 1


async def test_dequeue_timeout():
    """dequeue returns None on timeout."""
    q = PriorityQueue()
    result = await q.dequeue(timeout=0.1)
    assert result is None
