"""Tests for Layer 2 indicators."""
import pytest
from athena_x_ta_layer2_indicators import (
    EMAAgent, SMAAgent, VWAPAgent, RSIAgent,
    MACDAgent, ADXAgent, ATRAgent, BollingerAgent,
)
from athena_x_ta_base import Timeframe


async def test_ema_computes_value(repo):
    agent = EMAAgent(period=20)
    result = await agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)
    assert result.value is not None
    assert isinstance(result.value, float)
    assert result.confidence.score >= 0.9


async def test_sma_computes_value(repo):
    agent = SMAAgent(period=50)
    result = await agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)
    assert result.value is not None
    assert isinstance(result.value, float)


async def test_vwap_computes_value(repo):
    agent = VWAPAgent()
    result = await agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)
    assert result.value is not None
    assert isinstance(result.value, float)


async def test_rsi_computes_value(repo):
    agent = RSIAgent(period=14)
    result = await agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)
    assert result.value is not None
    assert 0 <= result.value <= 100


async def test_macd_computes_value(repo):
    agent = MACDAgent()
    result = await agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)
    assert result.value is not None
    assert "macd" in result.value
    assert "signal" in result.value
    assert "histogram" in result.value


async def test_adx_computes_value(repo):
    agent = ADXAgent(period=14)
    result = await agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)
    assert result.value is not None
    assert 0 <= result.value <= 100


async def test_atr_computes_value(repo):
    agent = ATRAgent(period=14)
    result = await agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)
    assert result.value is not None
    assert result.value > 0


async def test_bollinger_computes_value(repo):
    agent = BollingerAgent(period=20)
    result = await agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)
    assert result.value is not None
    assert "upper" in result.value
    assert "middle" in result.value
    assert "lower" in result.value
    assert "percent_b" in result.value


async def test_all_indicators_produce_confidence(repo):
    """Every indicator output includes confidence metadata."""
    agents = [
        EMAAgent(), SMAAgent(), VWAPAgent(), RSIAgent(),
        MACDAgent(), ADXAgent(), ATRAgent(), BollingerAgent(),
    ]
    for agent in agents:
        result = await agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)
        assert result.confidence is not None
        assert 0 <= result.confidence.score <= 1.0
        assert result.confidence.quality in ("A+", "A", "B", "C", "D", "F")


async def test_indicators_are_deterministic(repo):
    """Same input produces same output (deterministic)."""
    agent = EMAAgent(period=20)
    r1 = await agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)
    r2 = await agent.compute("SPY", Timeframe.FIFTEEN_MIN, repo)
    assert r1.value == r2.value


async def test_indicator_event_published(repo):
    """Indicators emit ai:technical:* events."""
    from athena_x_runtime_event_bus import InMemoryBusClient

    bus = InMemoryBusClient()
    agent = EMAAgent(period=20)

    received = []
    async def handler(event):
        received.append(event)
    await bus.subscribe("ai:technical:ema", handler)

    await agent.compute_and_publish("SPY", Timeframe.FIFTEEN_MIN, repo, event_bus=bus)

    assert len(received) == 1
    assert received[0].payload["indicator"] == "EMA20"
    assert "confidence" in received[0].payload
    await bus.close()
