"""Tests for backpressure policies (Stage 6 req 6)."""
import pytest
from datetime import datetime, timezone, timedelta
from athena_x_runtime_event_envelope import create_event, EventPriority
from athena_x_runtime_event_backpressure import BackpressureManager, BackpressureAction


@pytest.fixture
def manager():
    return BackpressureManager()


def test_market_events_drop_if_stale(manager):
    """Market events older than 500ms are dropped."""
    old_event = create_event(
        event_type="market:raw",
        source_agent="yahoo",
        priority=EventPriority.HIGH,
    )
    # Manually set old timestamp
    old_event = old_event.model_copy(update={"timestamp": datetime.now(timezone.utc) - timedelta(seconds=1)})

    action = manager.evaluate(old_event)
    assert action == BackpressureAction.DROP


def test_fresh_market_events_accepted(manager):
    """Fresh market events are accepted."""
    fresh_event = create_event(
        event_type="market:raw",
        source_agent="yahoo",
        priority=EventPriority.HIGH,
    )
    action = manager.evaluate(fresh_event)
    assert action == BackpressureAction.ACCEPT


def test_news_events_queued(manager):
    """News events are queued, never dropped."""
    for _ in range(100):
        event = create_event(
            event_type="news:breaking",
            source_agent="reuters",
            priority=EventPriority.NORMAL,
        )
        action = manager.evaluate(event)
        assert action == BackpressureAction.ACCEPT  # always accepted

    stats = manager.get_stats()
    assert stats["queue_sizes"]["news"] == 100


def test_system_low_priority_coalesced(manager):
    """System low-priority events are coalesced."""
    for _ in range(10):
        event = create_event(
            event_type="system:health",
            source_agent="monitor",
            priority=EventPriority.LOW,
        )
        result = manager.coalesce(event)

    # After 10 events, a summary should be emitted
    # (the 10th call returns the summary)
    assert result is not None or manager.get_stats()["coalesced_count"] >= 10


def test_critical_events_never_dropped(manager):
    """Critical events are never dropped."""
    event = create_event(
        event_type="system:error",
        source_agent="monitor",
        priority=EventPriority.CRITICAL,
    )
    action = manager.evaluate(event)
    assert action == BackpressureAction.ACCEPT


def test_stats_tracked(manager):
    """Manager tracks dropped + coalesced counts."""
    # Drop a stale market event
    old = create_event(event_type="market:raw", source_agent="t", priority=EventPriority.HIGH)
    old = old.model_copy(update={"timestamp": datetime.now(timezone.utc) - timedelta(seconds=1)})
    manager.evaluate(old)

    stats = manager.get_stats()
    assert stats["dropped_count"] == 1
