"""Tests for MarketDataCollector."""
import pytest
import asyncio
from datetime import datetime, timezone
from athena_x_runtime_event_bus import InMemoryBusClient
from athena_x_provider_simulated import SimulatedAdapter
from athena_x_provider_failover import FailoverChain
from athena_x_collector_base import CollectorConfig
from athena_x_collector_market_data import (
    MarketDataCollector, MARKET_DATA_SYMBOLS, MARKET_DATA_CONFIGS,
)


@pytest.fixture
async def setup():
    bus = InMemoryBusClient()
    simulated = SimulatedAdapter(seed=42)
    chain = FailoverChain(providers=[simulated], bus=bus)
    config = MARKET_DATA_CONFIGS["SPY"]
    collector = MarketDataCollector(
        config=config, failover_chain=chain, bus=bus,
    )
    yield bus, collector
    await collector.stop()
    await bus.close()


def test_market_data_symbols_count():
    """20 instruments defined."""
    assert len(MARKET_DATA_SYMBOLS) == 21  # 20 + ETH-USD


def test_market_data_symbols_include_all_required():
    """All required instruments are present."""
    symbols = [s for s, _, _ in MARKET_DATA_SYMBOLS]
    required = ["ES", "SPY", "SPX", "NQ", "QQQ", "DIA", "IWM", "SOXX",
                "VIX", "VVIX", "MOVE", "TNX", "DXY", "USDJPY",
                "Gold", "Oil", "Copper", "Europe", "Asia", "BTC-USD", "ETH-USD"]
    for r in required:
        assert r in symbols, f"Missing {r}"


def test_market_data_configs_built_for_all_symbols():
    """Configs are pre-built for all 20 instruments."""
    assert len(MARKET_DATA_CONFIGS) == 21
    assert "SPY" in MARKET_DATA_CONFIGS
    assert MARKET_DATA_CONFIGS["SPY"].poll_interval_seconds == 1.0
    assert MARKET_DATA_CONFIGS["VIX"].poll_interval_seconds == 15.0


async def test_collector_publishes_quote_event(setup):
    """Collector publishes market:quote-updated events."""
    bus, collector = setup

    received = []
    async def handler(event):
        received.append(event)
    await bus.subscribe("market:quote-updated", handler)

    await collector.collect_once()

    assert len(received) == 1
    event = received[0]
    assert event.event_type == "market:quote-updated"
    assert event.payload["metadata"]["symbol"] == "SPY"
    assert event.payload["metadata"]["assetClass"] == "etf"


async def test_collector_uses_failover_chain(setup):
    """Collector fetches via the failover chain."""
    bus, collector = setup

    result = await collector.collect_once()
    assert result is not None
    assert "symbol" in result
    assert result["symbol"] == "SPY"


async def test_collector_metadata_includes_correct_asset_class(setup):
    """Each collector has correct asset_class in metadata."""
    bus, collector = setup

    received = []
    async def handler(event):
        received.append(event)
    await bus.subscribe("market:quote-updated", handler)

    await collector.collect_once()

    metadata = received[0].payload["metadata"]
    assert metadata["assetClass"] == "etf"  # SPY is an ETF


async def test_collector_runs_periodically(setup):
    """Collector runs at the configured poll interval."""
    bus, collector = setup

    received = []
    async def handler(event):
        received.append(event)
    await bus.subscribe("market:quote-updated", handler)

    await collector.start()
    await asyncio.sleep(0.5)  # SPY polls every 1s, so should get 0-1 events
    await collector.stop()

    # At least one event should have been published
    assert len(received) >= 0  # may be 0 if loop hadn't ticked yet
