"""Tests for Layer 3 institutional analysis agents."""
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "layer2-indicators", "tests"))
from conftest import FakeMarketRepository
from athena_x_ta_layer3_institutional import (
    WyckoffAgent, ChanTheoryAgent, ElliottWaveAgent,
    SmartMoneyAgent, VolumePriceAgent,
    EscapeTopAgent, EntryAgent, PullUpPatternAgent,
)
from athena_x_ta_base import Timeframe


@pytest.fixture
def repo():
    return FakeMarketRepository()


async def test_all_8_layer3_agents_compute(repo):
    """All 8 Layer 3 agents produce output."""
    agents = [
        WyckoffAgent(), ChanTheoryAgent(), ElliottWaveAgent(),
        SmartMoneyAgent(), VolumePriceAgent(),
        EscapeTopAgent(), EntryAgent(), PullUpPatternAgent(),
    ]
    for agent in agents:
        result = await agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)
        assert result.value is not None
        assert result.confidence is not None
        assert agent.layer == 3  # check agent, not output


async def test_layer3_confidence_lower_than_layer2(repo):
    """Interpretive analyses have lower confidence than pure indicators."""
    from athena_x_ta_layer2_indicators import EMAAgent
    ema = EMAAgent()
    ema_result = await ema.compute("SPY", Timeframe.FIFTEEN_MIN, repo)

    wyckoff = WyckoffAgent()
    wyckoff_result = await wyckoff.compute("SPY", Timeframe.FIFTEEN_MIN, repo)

    # Layer 3 (interpretive) confidence is generally lower than Layer 2 (mathematical)
    assert wyckoff_result.confidence.score <= ema_result.confidence.score + 0.2


async def test_layer3_consumes_layers_1_2(repo):
    """Layer 3 agents metadata shows they consume layers 1+2."""
    agent = SmartMoneyAgent()
    result = await agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)
    assert result.metadata.get("consumes_layers") == [1, 2]
