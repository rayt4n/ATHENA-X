"""Tests for Layer 4 Multi-Timeframe Consensus."""
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "layer2-indicators", "tests"))
from conftest import FakeMarketRepository
from athena_x_ta_layer4_consensus import TimeframeConsensusAgent
from athena_x_ta_base import Timeframe


@pytest.fixture
def repo():
    return FakeMarketRepository()


async def test_consensus_produces_unified_view(repo):
    """Consensus agent produces a unified multi-timeframe view."""
    agent = TimeframeConsensusAgent()
    result = await agent.compute("SPY", Timeframe.DAILY, repo)
    assert result.value is not None
    assert "long_term" in result.value
    assert "intermediate" in result.value
    assert "intraday" in result.value
    assert "alignment" in result.value


async def test_alignment_score_between_0_and_100(repo):
    """Alignment score is 0-100."""
    agent = TimeframeConsensusAgent()
    result = await agent.compute("SPY", Timeframe.DAILY, repo)
    assert 0 <= result.value["alignment"] <= 100


async def test_conflicts_detected(repo):
    """Conflicts are detected when timeframes diverge."""
    agent = TimeframeConsensusAgent()
    result = await agent.compute("SPY", Timeframe.DAILY, repo)
    assert "conflicts" in result.value
    assert isinstance(result.value["conflicts"], list)


async def test_breakdown_includes_all_timeframes(repo):
    """Breakdown includes all 9 standard timeframes."""
    agent = TimeframeConsensusAgent()
    result = await agent.compute("SPY", Timeframe.DAILY, repo)
    breakdown = result.value["breakdown"]
    assert len(breakdown) == 9
    assert "1M" in breakdown
    assert "1m" in breakdown


async def test_consensus_confidence_includes_alignment(repo):
    """Confidence reflects alignment score."""
    agent = TimeframeConsensusAgent()
    result = await agent.compute("SPY", Timeframe.DAILY, repo)
    # Higher alignment -> higher confidence
    assert result.confidence.score > 0.5
