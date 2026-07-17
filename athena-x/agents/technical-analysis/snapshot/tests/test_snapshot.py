"""Tests for Technical Snapshot Agent."""
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "layer2-indicators", "tests"))
from conftest import FakeMarketRepository
from athena_x_ta_snapshot import TechnicalSnapshotAgent
from athena_x_ta_base import Timeframe


@pytest.fixture
def repo():
    return FakeMarketRepository()


async def test_snapshot_includes_all_layers(repo):
    """Snapshot includes data from all 5 layers."""
    agent = TechnicalSnapshotAgent()
    result = await agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)
    value = result.value
    # Layer 1
    assert "trend" in value
    assert "support" in value
    assert "resistance" in value
    # Layer 2
    assert "ema" in value
    assert "rsi" in value
    assert "macd" in value
    assert "atr" in value
    assert "bollinger" in value
    assert "adx" in value
    assert "vwap" in value
    # Layer 3
    assert "wyckoff_phase" in value
    assert "smart_money_signal" in value
    assert "entry_signal" in value
    # Layer 4
    assert "timeframe_consensus" in value
    assert "alignment_score" in value


async def test_snapshot_has_overall_confidence(repo):
    """Snapshot includes overall confidence."""
    agent = TechnicalSnapshotAgent()
    result = await agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)
    assert "overall_confidence" in result.value
    assert 0 < result.value["overall_confidence"] <= 1.0


async def test_snapshot_consumes_layers_1_to_4(repo):
    """Snapshot metadata shows it consumes layers 1-4."""
    agent = TechnicalSnapshotAgent()
    result = await agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)
    assert result.metadata.get("layers_consumed") == [1, 2, 3, 4]


async def test_snapshot_event_published(repo):
    """Snapshot emits ai:technical:technical_snapshot event."""
    from athena_x_runtime_event_bus import InMemoryBusClient

    bus = InMemoryBusClient()
    agent = TechnicalSnapshotAgent()

    received = []
    async def handler(event):
        received.append(event)
    await bus.subscribe("ai:technical:technical_snapshot", handler)

    await agent.compute_and_publish("SPY", Timeframe.FIFTEEN_MIN, repo, event_bus=bus)

    assert len(received) == 1
    assert "ema" in received[0].payload["value"]
    await bus.close()
