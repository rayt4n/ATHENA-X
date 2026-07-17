"""Tests for Layer 1 agents."""
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "layer2-indicators", "tests"))
from conftest import FakeMarketRepository
from athena_x_ta_layer1_market_structure import (
    TrendDetectionAgent, SwingHighLowAgent, SupportResistanceAgent,
    LiquidityAgent, VolumeProfileAgent, MultiTimeframeDataAgent,
)
from athena_x_ta_base import Timeframe


@pytest.fixture
def repo():
    return FakeMarketRepository()


async def test_trend_detection(repo):
    agent = TrendDetectionAgent()
    result = await agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)
    assert result.value in ("bullish", "bearish", "ranging")
    assert result.confidence.score > 0.7


async def test_swing_high_low(repo):
    agent = SwingHighLowAgent()
    result = await agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)
    assert result.value is not None
    assert "swing_highs" in result.value


async def test_support_resistance(repo):
    agent = SupportResistanceAgent()
    result = await agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)
    assert result.value is not None
    assert "resistance" in result.value
    assert "support" in result.value


async def test_liquidity(repo):
    agent = LiquidityAgent()
    result = await agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)
    assert result.value is not None
    assert "liquidity_pools" in result.value


async def test_volume_profile(repo):
    agent = VolumeProfileAgent()
    result = await agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)
    assert result.value is not None
    assert "poc" in result.value


async def test_multi_timeframe_data(repo):
    agent = MultiTimeframeDataAgent()
    result = await agent.compute("SPY", Timeframe.DAILY, repo)
    assert result.value is not None
    assert len(result.value) == 9  # 9 timeframes
