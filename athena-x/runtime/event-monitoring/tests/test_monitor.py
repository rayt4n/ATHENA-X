"""Tests for event monitor (Stage 6 req 8)."""
import pytest
import time
from athena_x_runtime_event_envelope import create_event, EventPriority
from athena_x_runtime_event_monitoring import EventMonitor


def test_record_publish_increments_count():
    monitor = EventMonitor()
    e = create_event(event_type="market:raw", source_agent="yahoo")
    monitor.record_publish(e)
    metrics = monitor.get_metrics()
    assert metrics.total_events_published == 1


def test_events_per_sec_computed():
    monitor = EventMonitor(window_seconds=1)
    for _ in range(10):
        monitor.record_publish(create_event(event_type="market:raw", source_agent="t"))
    metrics = monitor.get_metrics()
    assert metrics.events_per_sec > 0


def test_record_process_tracks_latency():
    monitor = EventMonitor()
    e = create_event(event_type="market:raw", source_agent="yahoo")
    monitor.record_process("consumer-1", e, latency_ms=5.0)
    metrics = monitor.get_metrics()
    assert metrics.total_events_processed == 1
    assert metrics.avg_latency_ms > 0


def test_slowest_consumers_identified():
    monitor = EventMonitor()
    e = create_event(event_type="market:raw", source_agent="t")
    # Fast consumer
    for _ in range(10):
        monitor.record_process("fast", e, latency_ms=1.0)
    # Slow consumer
    for _ in range(10):
        monitor.record_process("slow", e, latency_ms=100.0)

    metrics = monitor.get_metrics()
    assert len(metrics.slowest_consumers) > 0
    assert metrics.slowest_consumers[0]["consumer_id"] == "slow"


def test_dropped_events_tracked():
    monitor = EventMonitor()
    monitor.record_drop()
    monitor.record_drop()
    metrics = monitor.get_metrics()
    assert metrics.total_events_dropped == 2


def test_active_agents_counted():
    monitor = EventMonitor()
    monitor.record_publish(create_event(event_type="market:raw", source_agent="agent-1"))
    monitor.record_publish(create_event(event_type="market:raw", source_agent="agent-2"))
    monitor.record_publish(create_event(event_type="market:raw", source_agent="agent-1"))  # dup
    metrics = monitor.get_metrics()
    assert metrics.active_agents == 2


def test_by_category_breakdown():
    monitor = EventMonitor()
    monitor.record_publish(create_event(event_type="market:raw", source_agent="t"))
    monitor.record_publish(create_event(event_type="ai:forecast", source_agent="t"))
    monitor.record_publish(create_event(event_type="market:closed", source_agent="t"))
    metrics = monitor.get_metrics()
    assert metrics.by_category["market"] == 2
    assert metrics.by_category["ai"] == 1


def test_by_priority_breakdown():
    monitor = EventMonitor()
    monitor.record_publish(create_event(event_type="market:raw", source_agent="t", priority=EventPriority.CRITICAL))
    monitor.record_publish(create_event(event_type="market:raw", source_agent="t", priority=EventPriority.HIGH))
    monitor.record_publish(create_event(event_type="market:raw", source_agent="t", priority=EventPriority.HIGH))
    metrics = monitor.get_metrics()
    assert metrics.by_priority["critical"] == 1
    assert metrics.by_priority["high"] == 2
