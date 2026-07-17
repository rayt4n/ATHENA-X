"""Tests for OptionsDataCollector."""
import pytest
from datetime import datetime, timezone
from athena_x_runtime_event_bus import InMemoryBusClient
from athena_x_collector_base import CollectorConfig
from athena_x_collector_options_data import OptionsDataCollector, OPTIONS_DATA_TYPES
from athena_x_collector_options_data.types import OptionsDataType


@pytest.fixture
async def setup():
    bus = InMemoryBusClient()
    config = CollectorConfig(
        collector_id="options:NVDA",
        symbol="NVDA",
        asset_class="option",
        poll_interval_seconds=5.0,
    )
    collector = OptionsDataCollector(
        config=config, bus=bus, data_type=OptionsDataType.OPTION_CHAIN,
    )
    yield bus, collector
    await collector.stop()
    await bus.close()


def test_all_16_options_data_types_defined():
    """All 16 options data types are defined."""
    assert len(OPTIONS_DATA_TYPES) == 16


def test_options_data_types_include_raw_types():
    """Raw data types for downstream computation are included."""
    raw_types = [t for t in OPTIONS_DATA_TYPES if t.endswith("_raw")]
    assert "iv_rank_raw" in raw_types
    assert "gamma_exposure_raw" in raw_types
    assert "max_pain_raw" in raw_types
    assert "expected_move_raw" in raw_types


async def test_fetch_option_chain(setup):
    """Option chain fetch returns strikes with calls + puts."""
    bus, collector = setup
    data, ts = await collector.fetch_data()
    assert data["symbol"] == "NVDA"
    assert "chain" in data
    assert len(data["chain"]["strikes"]) == 21  # -10 to +10
    s = data["chain"]["strikes"][0]
    assert "call" in s and "put" in s
    assert "iv" in s["call"]


async def test_fetch_open_interest(setup):
    """Open interest fetch returns OI per strike."""
    bus, collector = setup
    collector._data_type = OptionsDataType.OPEN_INTEREST
    data, ts = await collector.fetch_data()
    assert "open_interest" in data
    assert len(data["open_interest"]) == 21


async def test_fetch_greeks(setup):
    """Greeks fetch returns delta/gamma per strike."""
    bus, collector = setup
    collector._data_type = OptionsDataType.GREEKS
    data, ts = await collector.fetch_data()
    assert "greeks" in data
    g = data["greeks"][0]
    assert "call_delta" in g
    assert "call_gamma" in g


async def test_fetch_iv(setup):
    """IV fetch returns ATM IV + per-strike."""
    bus, collector = setup
    collector._data_type = OptionsDataType.IV
    data, ts = await collector.fetch_data()
    assert "iv_atm" in data
    assert "iv_per_strike" in data


async def test_fetch_option_flow(setup):
    """Option flow returns unusual activity."""
    bus, collector = setup
    collector._data_type = OptionsDataType.OPTION_FLOW
    data, ts = await collector.fetch_data()
    assert "flow" in data
    assert len(data["flow"]) >= 1


async def test_fetch_dark_pool(setup):
    """Dark pool fetch returns prints."""
    bus, collector = setup
    collector._data_type = OptionsDataType.DARK_POOL
    data, ts = await collector.fetch_data()
    assert "dark_pool_prints" in data
    assert len(data["dark_pool_prints"]) >= 1


async def test_fetch_raw_for_computation(setup):
    """Raw data types return combined inputs for later computation."""
    bus, collector = setup
    collector._data_type = OptionsDataType.GAMMA_EXPOSURE_RAW
    data, ts = await collector.fetch_data()
    assert data["data_type"] == "gamma_exposure_raw"
    assert "spot" in data
    assert "strikes" in data
    s = data["strikes"][0]
    # Raw data for GEX includes OI + gamma
    assert "call_oi" in s
    assert "call_gamma" in s


async def test_collector_publishes_options_event(setup):
    """Collector publishes options:chain-refreshed events."""
    bus, collector = setup

    received = []
    async def handler(event):
        received.append(event)
    await bus.subscribe("options:chain-refreshed", handler)

    await collector.collect_once()

    assert len(received) == 1
    assert received[0].payload["metadata"]["symbol"] == "NVDA"
    assert received[0].payload["metadata"]["assetClass"] == "option"
