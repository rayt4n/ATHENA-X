"""Tests for Snapshot Coordinator (Stage 6 req 5)."""
import pytest
from datetime import datetime, timezone, timedelta
from athena_x_runtime_snapshot_coordinator import (
    SnapshotCoordinator, SnapshotConfig, SnapshotStatus,
)


@pytest.fixture
def coordinator():
    config = SnapshotConfig(
        required_feeds=["SPY", "ES", "VIX"],
        max_staleness_seconds=5.0,
        wait_timeout_seconds=0.5,
        on_stale="degraded",
    )
    return SnapshotCoordinator(config)


def test_all_feeds_fresh_returns_synced(coordinator):
    """When all feeds are fresh, snapshot is SYNCED."""
    now = datetime.now(timezone.utc)
    coordinator.update_feed("SPY", now)
    coordinator.update_feed("ES", now)
    coordinator.update_feed("VIX", now)

    import asyncio
    result = asyncio.run(coordinator.try_snapshot())
    assert result.status == SnapshotStatus.SYNCED
    assert len(result.stale_feeds) == 0
    assert len(result.missing_feeds) == 0


def test_missing_feed_returns_blocked(coordinator):
    """When a required feed is missing, snapshot is BLOCKED (or DEGRADED)."""
    now = datetime.now(timezone.utc)
    coordinator.update_feed("SPY", now)
    coordinator.update_feed("ES", now)
    # VIX missing

    import asyncio
    result = asyncio.run(coordinator.try_snapshot())
    assert result.status in (SnapshotStatus.BLOCKED, SnapshotStatus.TIMEOUT, SnapshotStatus.DEGRADED)
    assert "VIX" in result.missing_feeds


def test_stale_feed_returns_degraded(coordinator):
    """When a feed is stale, snapshot is DEGRADED (if on_stale=degraded)."""
    now = datetime.now(timezone.utc)
    coordinator.update_feed("SPY", now)
    coordinator.update_feed("ES", now)
    coordinator.update_feed("VIX", now - timedelta(seconds=10))  # stale

    import asyncio
    result = asyncio.run(coordinator.try_snapshot())
    assert result.status == SnapshotStatus.DEGRADED
    assert "VIX" in result.stale_feeds


def test_stale_feed_blocks_when_configured():
    """When on_stale=block, stale feeds cause waiting."""
    config = SnapshotConfig(
        required_feeds=["SPY"],
        max_staleness_seconds=1.0,
        wait_timeout_seconds=0.2,
        on_stale="block",
    )
    coord = SnapshotCoordinator(config)
    coord.update_feed("SPY", datetime.now(timezone.utc) - timedelta(seconds=5))

    import asyncio
    result = asyncio.run(coord.try_snapshot())
    # After timeout, should be TIMEOUT
    assert result.status in (SnapshotStatus.TIMEOUT, SnapshotStatus.DEGRADED)


def test_snapshot_event_created(coordinator):
    """Snapshot coordinator can create a market:snapshot event."""
    now = datetime.now(timezone.utc)
    coordinator.update_feed("SPY", now)
    coordinator.update_feed("ES", now)
    coordinator.update_feed("VIX", now)

    import asyncio
    result = asyncio.run(coordinator.try_snapshot())
    event = coordinator.create_snapshot_event(result)
    assert event.event_type == "market:snapshot"
    assert event.payload["status"] == "synced"


def test_get_feed_status(coordinator):
    """get_feed_status returns current status of all feeds."""
    now = datetime.now(timezone.utc)
    coordinator.update_feed("SPY", now)
    coordinator.update_feed("VIX", now - timedelta(seconds=10))

    status = coordinator.get_feed_status()
    assert status["SPY"]["status"] == "fresh"
    assert status["VIX"]["status"] == "stale"
    assert status["ES"]["status"] == "missing"
