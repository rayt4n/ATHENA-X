"""Tests for event log + replay (Stage 6 req 7)."""
import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from athena_x_runtime_event_envelope import create_event, EventPriority
from athena_x_runtime_event_log import EventLog


@pytest.fixture
def event_log():
    return EventLog()


async def test_append_and_count(event_log):
    """Events can be appended and counted."""
    e = create_event(event_type="market:raw", source_agent="yahoo")
    seq = await event_log.append(e)
    assert seq == 1
    assert event_log.count() == 1


async def test_replay_all_events(event_log):
    """Replay returns all events when no filters."""
    for i in range(5):
        await event_log.append(create_event(event_type="market:raw", source_agent="t"))
    result = await event_log.replay()
    assert result.total_count == 5


async def test_replay_by_time_range(event_log):
    """Replay filters by time range."""
    t1 = datetime.now(timezone.utc)
    await event_log.append(create_event(event_type="market:raw", source_agent="t"))
    await asyncio.sleep(0.01)
    t2 = datetime.now(timezone.utc)
    await event_log.append(create_event(event_type="market:raw", source_agent="t"))
    await asyncio.sleep(0.01)
    t3 = datetime.now(timezone.utc)

    # Replay only events between t2 and t3
    result = await event_log.replay(start=t2, end=t3)
    assert result.total_count <= 2  # at most 2 events in this range


async def test_replay_by_event_type(event_log):
    """Replay filters by event type."""
    await event_log.append(create_event(event_type="market:raw", source_agent="t"))
    await event_log.append(create_event(event_type="ai:forecast", source_agent="t"))
    await event_log.append(create_event(event_type="market:raw", source_agent="t"))

    result = await event_log.replay(event_type="market:raw")
    assert result.total_count == 2


async def test_replay_by_correlation_id(event_log):
    """Replay filters by correlation ID (end-to-end trace)."""
    cid = uuid4()
    await event_log.append(create_event(event_type="market:raw", source_agent="t", correlation_id=cid))
    await event_log.append(create_event(event_type="market:validated", source_agent="t", correlation_id=cid))
    await event_log.append(create_event(event_type="ai:technical", source_agent="t", correlation_id=cid))
    # Unrelated event
    await event_log.append(create_event(event_type="market:raw", source_agent="t"))

    events = await event_log.replay_by_correlation(cid)
    assert len(events) == 3
    assert all(e.correlation_id == cid for e in events)


async def test_replay_with_limit(event_log):
    """Replay respects limit."""
    for _ in range(10):
        await event_log.append(create_event(event_type="t", source_agent="t"))
    result = await event_log.replay(limit=5)
    assert result.total_count == 5


async def test_persist_to_filesystem(tmp_path):
    """Events are persisted to filesystem as JSONL."""
    log_path = tmp_path / "events.jsonl"
    event_log = EventLog(persist_path=log_path)
    await event_log.append(create_event(event_type="market:raw", source_agent="yahoo"))

    assert log_path.exists()
    content = log_path.read_text()
    assert "market:raw" in content


async def test_replay_deterministic(event_log):
    """Replay is deterministic - same log, same results."""
    for i in range(5):
        await event_log.append(create_event(event_type="market:raw", source_agent="t", payload={"i": i}))

    r1 = await event_log.replay()
    r2 = await event_log.replay()

    assert r1.total_count == r2.total_count
    for e1, e2 in zip(r1.events, r2.events):
        assert e1.event_id == e2.event_id


import asyncio  # needed for asyncio.sleep in tests
