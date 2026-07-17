"""Tests for Layer 5 Technical Supervisor."""
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "layer2-indicators", "tests"))
from conftest import FakeMarketRepository
from athena_x_ta_layer5_supervisor import TechnicalSupervisor
from athena_x_ta_layer2_indicators import EMAAgent, RSIAgent
from athena_x_ta_base import Timeframe


@pytest.fixture
def repo():
    return FakeMarketRepository()


async def test_supervisor_monitors_registered_agents(repo):
    """Supervisor monitors all registered agents."""
    sup = TechnicalSupervisor()
    ema = EMAAgent()
    rsi = RSIAgent()
    sup.register_agent(ema)
    sup.register_agent(rsi)

    result = await sup.compute("SPY", Timeframe.DAILY, repo)
    assert result.value["total_agents"] == 2


async def test_supervisor_detects_failed_agents(repo):
    """Supervisor detects agents that haven't computed."""
    sup = TechnicalSupervisor()
    ema = EMAAgent()  # never computed
    sup.register_agent(ema)

    result = await sup.compute("SPY", Timeframe.DAILY, repo)
    assert "ema" in result.value["failed_agents"]


async def test_supervisor_reports_active_agents(repo):
    """Supervisor reports active agents after computation."""
    sup = TechnicalSupervisor()
    ema = EMAAgent()
    sup.register_agent(ema)

    # Run the agent
    await ema.compute("SPY", Timeframe.FIFTEEN_MIN, repo)

    result = await sup.compute("SPY", Timeframe.DAILY, repo)
    assert result.value["active_agents"] == 1
    assert result.value["failed_agents"] == []


async def test_supervisor_publishes_health_events(repo):
    """Supervisor publishes health events for failures."""
    sup = TechnicalSupervisor()
    ema = EMAAgent()  # never computed
    sup.register_agent(ema)

    result = await sup.compute("SPY", Timeframe.DAILY, repo)
    events = result.value["health_events"]
    assert any(e["type"] == "agents_failed" for e in events)
