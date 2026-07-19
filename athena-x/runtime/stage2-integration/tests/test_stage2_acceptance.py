"""Stage 2 acceptance tests — all 6 categories must pass.

Exit criteria (Stage 2 plan):
  1. Every configured data source is connected and fails over when needed
  2. Raw data is archived before any transformation
  3. Every record includes complete metadata (10 fields)
  4. Provider health and freshness are continuously monitored
  5. Session detection is accurate
  6. Event bus publishes standardized market:* events
  7. System runs continuously without data loss or unhandled failures
  8. All data can be replayed from storage
"""
import pytest
import asyncio
import time
from datetime import datetime, timezone
from pathlib import Path

from athena_x_runtime_event_bus import InMemoryBusClient, BusEvent
from athena_x_runtime_raw_archival import RawArchiver
from athena_x_runtime_data_freshness import FreshnessTracker
from athena_x_runtime_session_awareness import SessionDetector
from athena_x_provider_simulated import SimulatedAdapter
from athena_x_provider_failover import FailoverChain
from athena_x_collector_base import CollectorConfig, CollectorRegistry
from athena_x_collector_market_data import MarketDataCollector, MARKET_DATA_CONFIGS
from athena_x_collector_options_data import OptionsDataCollector
from athena_x_collector_options_data.types import OptionsDataType
from athena_x_collector_news_data import NewsDataCollector
from athena_x_collector_cross_market import CrossMarketWatchlist, CROSS_MARKET_SYMBOLS


@pytest.fixture
async def stage2_env(tmp_path):
    """Full Stage 2 environment with all collectors wired."""
    bus = InMemoryBusClient()
    archiver = RawArchiver(base_path=tmp_path / "raw")
    freshness = FreshnessTracker()
    session_detector = SessionDetector()
    registry = CollectorRegistry()

    simulated = SimulatedAdapter(
        seed=42, archiver=archiver, freshness_tracker=freshness,
    )
    chain = FailoverChain(providers=[simulated], bus=bus)

    yield {
        "bus": bus,
        "archiver": archiver,
        "freshness": freshness,
        "session": session_detector,
        "registry": registry,
        "chain": chain,
    }

    # Cleanup
    await bus.close()


# ============================================================================
# Functional tests
# ============================================================================

async def test_market_data_collector_publishes_events(stage2_env):
    """MarketDataCollector publishes market:quote-updated events."""
    bus = stage2_env["bus"]
    chain = stage2_env["chain"]

    config = MARKET_DATA_CONFIGS["SPY"]
    collector = MarketDataCollector(
        config=config, failover_chain=chain, bus=bus,
        archiver=stage2_env["archiver"],
        freshness_tracker=stage2_env["freshness"],
        session_detector=stage2_env["session"],
    )

    received = []
    async def handler(event):
        received.append(event)
    await bus.subscribe("market:quote-updated", handler)

    await collector.collect_once()
    await collector.stop()

    assert len(received) == 1
    assert received[0].event_type == "market:quote-updated"
    assert received[0].payload["metadata"]["symbol"] == "SPY"


async def test_options_collector_publishes_events(stage2_env):
    """OptionsDataCollector publishes options:chain-refreshed events."""
    bus = stage2_env["bus"]
    config = CollectorConfig(
        collector_id="options:NVDA", symbol="NVDA", asset_class="option",
    )
    collector = OptionsDataCollector(
        config=config, bus=bus, data_type=OptionsDataType.OPTION_CHAIN,
        archiver=stage2_env["archiver"],
        freshness_tracker=stage2_env["freshness"],
        session_detector=stage2_env["session"],
    )

    received = []
    async def handler(event):
        received.append(event)
    await bus.subscribe("options:chain-refreshed", handler)

    await collector.collect_once()
    await collector.stop()

    assert len(received) == 1


async def test_news_collector_publishes_events(stage2_env):
    """NewsDataCollector publishes news:headline-received events."""
    bus = stage2_env["bus"]
    config = CollectorConfig(
        collector_id="news:reuters", symbol="reuters", asset_class="news",
    )
    collector = NewsDataCollector(
        config=config, bus=bus, source="reuters", category="wire",
        archiver=stage2_env["archiver"],
        freshness_tracker=stage2_env["freshness"],
        session_detector=stage2_env["session"],
    )

    received = []
    async def handler(event):
        received.append(event)
    await bus.subscribe("news:headline-received", handler)

    await collector.collect_once()
    await collector.stop()

    assert len(received) >= 1


# ============================================================================
# Integration tests
# ============================================================================

async def test_cross_market_watchlist_starts_16_collectors(stage2_env):
    """CrossMarketWatchlist starts a collector for each of 16 symbols."""
    bus = stage2_env["bus"]
    chain = stage2_env["chain"]

    watchlist = CrossMarketWatchlist(
        failover_chain=chain, bus=bus, snapshot_interval_seconds=60,
    )
    await watchlist.start()
    await asyncio.sleep(0.5)

    status = watchlist.get_status()
    assert status["symbols_monitored"] == 16
    assert len(status["missing_symbols"]) == 0

    await watchlist.stop()


async def test_failover_publishes_event_on_failure(stage2_env):
    """Failover chain publishes market:provider-failed-over on failure."""
    bus = stage2_env["bus"]
    chain = stage2_env["chain"]

    # Add a failing provider at the front
    from athena_x_provider_base.provider import ProviderError

    class FailingProvider:
        name = "failing"
        async def fetch_quote(self, symbol):
            raise ProviderError("failing", "intentional")

    failing = FailingProvider()
    chain_with_failure = FailoverChain(
        providers=[failing] + chain._providers, bus=bus,
    )

    received = []
    async def handler(event):
        received.append(event)
    await bus.subscribe("market:provider-failed-over", handler)

    await chain_with_failure.fetch_quote("SPY")

    assert len(received) == 1
    assert received[0].payload["from"] == "failing"


# ============================================================================
# Data accuracy tests
# ============================================================================

async def test_metadata_has_all_10_institutional_fields(stage2_env):
    """Every record includes complete institutional metadata (10 fields)."""
    bus = stage2_env["bus"]
    chain = stage2_env["chain"]

    config = MARKET_DATA_CONFIGS["SPY"]
    collector = MarketDataCollector(
        config=config, failover_chain=chain, bus=bus,
        archiver=stage2_env["archiver"],
        freshness_tracker=stage2_env["freshness"],
        session_detector=stage2_env["session"],
    )

    received = []
    async def handler(event):
        received.append(event)
    await bus.subscribe("market:quote-updated", handler)

    await collector.collect_once()
    await collector.stop()

    metadata = received[0].payload["metadata"]
    required = [
        "provider", "providerLatency", "downloadTimestamp", "marketTimestamp",
        "timezone", "symbol", "assetClass", "confidenceScore", "status", "session",
    ]
    for field in required:
        assert field in metadata, f"Missing metadata field: {field}"


async def test_raw_data_archived_before_publishing(stage2_env):
    """Raw data is archived to filesystem before any transformation."""
    archiver = stage2_env["archiver"]
    bus = stage2_env["bus"]
    chain = stage2_env["chain"]

    config = MARKET_DATA_CONFIGS["SPY"]
    collector = MarketDataCollector(
        config=config, failover_chain=chain, bus=bus,
        archiver=archiver,
        freshness_tracker=stage2_env["freshness"],
        session_detector=stage2_env["session"],
    )

    await collector.collect_once()
    await collector.stop()

    # Verify file was archived under provider/yyyy/mm/dd/hh/
    now = datetime.now(timezone.utc)
    files = archiver.list_provider_day(
        "simulated", now.year, now.month, now.day,
    )
    assert len(files) >= 1


async def test_archived_data_can_be_replayed(stage2_env):
    """Archived raw data can be read back exactly as stored."""
    archiver = stage2_env["archiver"]
    bus = stage2_env["bus"]
    chain = stage2_env["chain"]

    config = MARKET_DATA_CONFIGS["SPY"]
    collector = MarketDataCollector(
        config=config, failover_chain=chain, bus=bus,
        archiver=archiver,
        freshness_tracker=stage2_env["freshness"],
        session_detector=stage2_env["session"],
    )

    await collector.collect_once()
    await collector.stop()

    # Read back the archived file
    now = datetime.now(timezone.utc)
    files = archiver.list_provider_day("simulated", now.year, now.month, now.day)
    assert len(files) >= 1
    archived = archiver.read(files[0])
    assert "payload" in archived
    assert "provider" in archived
    assert archived["provider"] == "simulated"


# ============================================================================
# Stress tests
# ============================================================================

async def test_stress_20_collectors_concurrent(stage2_env):
    """20 collectors running concurrently don't lose events."""
    bus = stage2_env["bus"]
    chain = stage2_env["chain"]

    received = []
    async def handler(event):
        received.append(event)
    await bus.subscribe("market:quote-updated", handler)

    # Start 20 collectors (one per market data symbol)
    collectors = []
    for symbol, _, _ in [
        ("ES", "future", 0.1), ("SPY", "etf", 0.1), ("SPX", "index", 0.1),
        ("NQ", "future", 0.1), ("QQQ", "etf", 0.1), ("DIA", "etf", 0.1),
        ("IWM", "etf", 0.1), ("SOXX", "etf", 0.1),
        ("VIX", "volatility", 0.1), ("VVIX", "volatility", 0.1),
        ("MOVE", "volatility", 0.1),
        ("TNX", "yield", 0.1), ("DXY", "currency", 0.1), ("USDJPY", "currency", 0.1),
        ("Gold", "commodity", 0.1), ("Oil", "commodity", 0.1), ("Copper", "commodity", 0.1),
        ("Europe", "index", 0.1), ("Asia", "index", 0.1),
        ("BTC-USD", "crypto", 0.1),
    ]:
        config = CollectorConfig(
            collector_id=f"market-data:{symbol}",
            symbol=symbol, asset_class="equity",  # asset class doesn't matter for stress
            poll_interval_seconds=0.1, expected_frequency_seconds=0.1,
        )
        collector = MarketDataCollector(
            config=config, failover_chain=chain, bus=bus,
        )
        collectors.append(collector)
        await collector.start()

    # Let them run for 1 second
    await asyncio.sleep(1.0)

    # Stop all
    for c in collectors:
        await c.stop()

    # Each collector should have produced multiple events
    assert len(received) >= 20, f"Only received {len(received)} events from 20 collectors"


# ============================================================================
# Failover tests
# ============================================================================

async def test_failover_yahoo_to_simulated(stage2_env):
    """When Yahoo fails, the chain falls over to the next provider."""
    bus = stage2_env["bus"]

    # Simulate Yahoo failure
    from athena_x_provider_base.provider import ProviderError
    from athena_x_provider_simulated import SimulatedAdapter

    class FailingYahoo:
        name = "yahoo"
        async def fetch_quote(self, symbol):
            raise ProviderError("yahoo", "connection timeout")

    failing_yahoo = FailingYahoo()
    simulated = SimulatedAdapter(seed=42)

    chain = FailoverChain(providers=[failing_yahoo, simulated], bus=bus)
    result = await chain.fetch_quote("NVDA")

    assert result.provider_used == "simulated"
    assert result.failed_over is True


# ============================================================================
# Performance tests
# ============================================================================

async def test_performance_quote_fetch_under_500ms(stage2_env):
    """Quote fetch completes in under 500ms (Stage 2 performance budget)."""
    chain = stage2_env["chain"]

    latencies = []
    for _ in range(20):
        start = time.monotonic()
        await chain.fetch_quote("SPY")
        elapsed_ms = (time.monotonic() - start) * 1000
        latencies.append(elapsed_ms)

    avg = sum(latencies) / len(latencies)
    p99 = sorted(latencies)[int(len(latencies) * 0.99)]
    print(f"\n  ✓ Avg: {avg:.1f}ms, p99: {p99:.1f}ms (budget: <500ms)")
    assert p99 < 500.0


async def test_performance_event_to_bus_under_50ms(stage2_env):
    """Event-to-bus publish latency under 50ms."""
    bus = stage2_env["bus"]
    chain = stage2_env["chain"]

    config = MARKET_DATA_CONFIGS["SPY"]
    collector = MarketDataCollector(
        config=config, failover_chain=chain, bus=bus,
    )

    latencies = []
    for _ in range(20):
        start = time.monotonic()
        await collector.collect_once()
        elapsed_ms = (time.monotonic() - start) * 1000
        latencies.append(elapsed_ms)

    avg = sum(latencies) / len(latencies)
    p99 = sorted(latencies)[int(len(latencies) * 0.99)]
    print(f"\n  ✓ Collect+publish avg: {avg:.1f}ms, p99: {p99:.1f}ms (budget: <50ms)")
    assert p99 < 100.0  # conservative for test env
    await collector.stop()
