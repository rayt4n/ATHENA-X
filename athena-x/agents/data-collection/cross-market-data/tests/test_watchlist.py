"""Tests for CrossMarketWatchlist."""
import pytest
import asyncio
from athena_x_runtime_event_bus import InMemoryBusClient
from athena_x_provider_simulated import SimulatedAdapter
from athena_x_provider_failover import FailoverChain
from athena_x_collector_cross_market import CrossMarketWatchlist, CROSS_MARKET_SYMBOLS


@pytest.fixture
async def setup():
    bus = InMemoryBusClient()
    simulated = SimulatedAdapter(seed=42)
    chain = FailoverChain(providers=[simulated], bus=bus)
    watchlist = CrossMarketWatchlist(
        failover_chain=chain, bus=bus, snapshot_interval_seconds=1,
    )
    yield bus, watchlist
    await watchlist.stop()
    await bus.close()


def test_16_cross_market_symbols():
    """16 instruments in the cross-market watchlist."""
    assert len(CROSS_MARKET_SYMBOLS) == 16
    expected = ["SPY", "ES", "SPX", "NQ", "QQQ", "DIA", "IWM", "SOXX",
                "VIX", "VVIX", "TNX", "DXY", "Gold", "Oil", "Copper", "USDJPY"]
    for s in expected:
        assert s in CROSS_MARKET_SYMBOLS


async def test_watchlist_starts_all_collectors(setup):
    """Watchlist starts a collector for each of the 16 symbols."""
    bus, watchlist = setup
    await watchlist.start()
    await asyncio.sleep(0.5)

    status = watchlist.get_status()
    assert status["running"] is True
    assert status["symbols_monitored"] == 16
    assert len(status["missing_symbols"]) == 0


async def test_watchlist_publishes_snapshot(setup):
    """Watchlist publishes cross-market:symbol-state-updated events."""
    bus, watchlist = setup

    received = []
    async def handler(event):
        received.append(event)
    await bus.subscribe("cross-market:symbol-state-updated", handler)

    await watchlist.start()
    # Wait for collectors to publish quotes + snapshot to fire
    await asyncio.sleep(2.5)

    assert len(received) >= 1
    event = received[0]
    assert event.event_type == "cross-market:symbol-state-updated"
    assert "symbol" in event.payload
    assert "state" in event.payload


async def test_watchlist_get_status(setup):
    """get_status returns expected structure."""
    bus, watchlist = setup
    await watchlist.start()
    await asyncio.sleep(0.3)

    status = watchlist.get_status()
    assert "running" in status
    assert "symbols_monitored" in status
    assert "symbols_with_data" in status
    assert "expected_symbols" in status
    assert "missing_symbols" in status
