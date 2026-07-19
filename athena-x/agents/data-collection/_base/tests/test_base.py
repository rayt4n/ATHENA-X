"""Tests for BaseCollector framework."""
import pytest
import asyncio
from datetime import datetime, timezone
from athena_x_runtime_event_bus import InMemoryBusClient, BusEvent
from athena_x_runtime_raw_archival import RawArchiver
from athena_x_runtime_data_freshness import FreshnessTracker
from athena_x_collector_base import BaseCollector, CollectorConfig, CollectorRegistry


class FakeCollector(BaseCollector):
    """Test collector that yields incrementing values."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._counter = 0

    async def fetch_data(self):
        self._counter += 1
        return {"symbol": self.symbol, "value": self._counter}, datetime.now(timezone.utc)

    def _get_provider_name(self) -> str:
        return "simulated"


@pytest.fixture
async def setup():
    bus = InMemoryBusClient()
    archiver = RawArchiver(base_path="/tmp/test_archival")
    freshness = FreshnessTracker()
    config = CollectorConfig(
        collector_id="test:NVDA",
        symbol="NVDA",
        asset_class="equity",
        poll_interval_seconds=0.1,
        expected_frequency_seconds=0.1,
    )
    collector = FakeCollector(
        config=config, bus=bus, archiver=archiver, freshness_tracker=freshness,
    )
    yield bus, archiver, freshness, collector
    await collector.stop()
    await bus.close()


async def test_collector_publishes_events(setup):
    """Collector publishes market:quote-updated events on each collect."""
    bus, archiver, freshness, collector = setup

    received = []
    async def handler(event):
        received.append(event)
    await bus.subscribe("market:quote-updated", handler)

    await collector.start()
    await asyncio.sleep(0.5)

    assert len(received) >= 1
    event = received[0]
    assert event.event_type == "market:quote-updated"
    assert event.payload["metadata"]["symbol"] == "NVDA"
    assert event.payload["metadata"]["provider"] == "simulated"
    assert "data" in event.payload


async def test_collector_archives_raw_payload(setup):
    """Collector archives raw payloads via RawArchiver."""
    bus, archiver, freshness, collector = setup

    await collector.start()
    await asyncio.sleep(0.3)
    await collector.stop()

    files = list(archiver.list_provider_day("simulated",
                                             datetime.now(timezone.utc).year,
                                             datetime.now(timezone.utc).month,
                                             datetime.now(timezone.utc).day))
    assert len(files) >= 1


async def test_collector_tracks_freshness(setup):
    """Collector records receipts in FreshnessTracker."""
    bus, archiver, freshness, collector = setup

    await collector.start()
    await asyncio.sleep(0.3)
    await collector.stop()

    # Stream ID is {collector_id}:{symbol} = "test:NVDA:NVDA"
    stats = freshness.get_stats("test:NVDA:NVDA")
    assert stats is not None
    assert stats.total_received >= 1
    assert stats.status.value == "fresh"


async def test_collector_emits_heartbeats(setup):
    """Collector emits system:agent-heartbeat events."""
    bus, archiver, freshness, collector = setup

    heartbeats = []
    async def handler(event):
        heartbeats.append(event)
    await bus.subscribe("system:agent-heartbeat", handler)

    await collector.start()
    await asyncio.sleep(0.3)
    await collector.stop()

    assert len(heartbeats) >= 1
    hb = heartbeats[0]
    assert hb.payload["agentId"] == "test:NVDA"
    assert hb.payload["metrics"]["running"] in (True, False)


async def test_collector_metadata_has_10_fields(setup):
    """Each event payload includes complete institutional metadata."""
    bus, archiver, freshness, collector = setup

    received = []
    async def handler(event):
        received.append(event)
    await bus.subscribe("market:quote-updated", handler)

    await collector.collect_once()

    event = received[0]
    metadata = event.payload["metadata"]
    # 10 mandatory fields
    assert metadata["provider"] == "simulated"
    assert "providerLatency" in metadata
    assert "downloadTimestamp" in metadata
    assert "marketTimestamp" in metadata
    assert "timezone" in metadata
    assert metadata["symbol"] == "NVDA"
    assert "assetClass" in metadata
    assert "confidenceScore" in metadata
    assert "status" in metadata
    assert "session" in metadata


async def test_collector_error_count_tracked(setup):
    """Collector tracks error count on failures."""
    bus, archiver, freshness, collector = setup

    # Override fetch_data to fail
    async def failing_fetch():
        raise RuntimeError("intentional failure")
    collector.fetch_data = failing_fetch

    with pytest.raises(RuntimeError):
        await collector.collect_once()

    assert collector._error_count == 1


def test_registry():
    """CollectorRegistry tracks collectors."""
    reg = CollectorRegistry()

    class FakeColl(BaseCollector):
        async def fetch_data(self):
            return {}, datetime.now(timezone.utc)
        def _get_provider_name(self):
            return "test"

    config = CollectorConfig(
        collector_id="test:A", symbol="A", asset_class="equity",
    )
    bus = InMemoryBusClient()
    c = FakeColl(config=config, bus=bus)

    reg.register(c)
    assert len(reg.list_all()) == 1
    assert reg.get("test:A") is c
    assert len(reg.list_by_symbol("A")) == 1

    reg.unregister("test:A")
    assert len(reg.list_all()) == 0
