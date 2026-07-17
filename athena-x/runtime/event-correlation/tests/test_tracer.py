"""Tests for correlation tracer (Stage 6 req 4)."""
import pytest
from uuid import uuid4
from athena_x_runtime_event_envelope import create_event, EventPriority
from athena_x_runtime_event_correlation import CorrelationTracer


def test_track_and_get_trace():
    """Events are tracked by correlation ID."""
    tracer = CorrelationTracer()
    cid = uuid4()

    e1 = create_event(event_type="market:raw", source_agent="yahoo", correlation_id=cid, symbol="SPY")
    e2 = create_event(event_type="market:validated", source_agent="validator", correlation_id=cid)
    e3 = create_event(event_type="ai:technical", source_agent="ta.rsi", correlation_id=cid)

    tracer.track(e1)
    tracer.track(e2)
    tracer.track(e3)

    trace = tracer.get_trace(cid)
    assert len(trace) == 3
    assert trace[0].event_type == "market:raw"
    assert trace[1].event_type == "market:validated"
    assert trace[2].event_type == "ai:technical"


def test_different_correlation_ids_tracked_separately():
    """Different correlation IDs are tracked separately."""
    tracer = CorrelationTracer()
    cid1 = uuid4()
    cid2 = uuid4()

    tracer.track(create_event(event_type="market:raw", source_agent="t", correlation_id=cid1))
    tracer.track(create_event(event_type="market:raw", source_agent="t", correlation_id=cid2))

    assert len(tracer.get_trace(cid1)) == 1
    assert len(tracer.get_trace(cid2)) == 1


def test_trace_summary():
    """Trace summary includes event count, agents, duration."""
    tracer = CorrelationTracer()
    cid = uuid4()

    tracer.track(create_event(event_type="market:raw", source_agent="yahoo", correlation_id=cid, symbol="SPY"))
    tracer.track(create_event(event_type="ai:technical", source_agent="ta.rsi", correlation_id=cid))

    summary = tracer.get_trace_summary(cid)
    assert summary["event_count"] == 2
    assert "yahoo" in summary["agents_involved"]
    assert "ta.rsi" in summary["agents_involved"]
    assert "SPY" in summary["symbols"]
    assert summary["duration_ms"] >= 0


def test_create_child_event_shares_correlation():
    """Child events share the parent's correlation ID."""
    tracer = CorrelationTracer()
    parent = create_event(event_type="market:raw", source_agent="yahoo", symbol="SPY")

    child = tracer.create_child_event(
        parent=parent,
        event_type="market:validated",
        source_agent="validator",
        payload={"status": "verified"},
    )
    assert child.correlation_id == parent.correlation_id
    assert child.event_id != parent.event_id
    assert child.symbol == parent.symbol


def test_active_correlations_count():
    tracer = CorrelationTracer()
    assert tracer.active_correlations() == 0

    tracer.track(create_event(event_type="t", source_agent="t", correlation_id=uuid4()))
    assert tracer.active_correlations() == 1

    tracer.track(create_event(event_type="t", source_agent="t", correlation_id=uuid4()))
    assert tracer.active_correlations() == 2


def test_trace_for_nonexistent_correlation():
    """Nonexistent correlation ID returns empty trace."""
    tracer = CorrelationTracer()
    trace = tracer.get_trace(uuid4())
    assert trace == []
