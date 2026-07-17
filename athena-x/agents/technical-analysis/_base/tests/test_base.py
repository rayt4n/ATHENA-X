"""Tests for TA base infrastructure."""
import pytest
from datetime import datetime, timezone, timedelta
from athena_x_ta_base import (
    BaseTAAgent, TAOutput, TAConfidence,
    BarCache, CachedBars,
    STANDARD_TIMEFRAMES, TimeframeContext, Timeframe,
)


class FakeTAAgent(BaseTAAgent):
    """Fake TA agent for testing."""
    def __init__(self, **kwargs):
        super().__init__(name="fake", layer=2, **kwargs)

    async def compute(self, symbol, timeframe, repo):
        return TAOutput(
            agent=self.name, symbol=symbol, timeframe=timeframe.value,
            indicator="FAKE", value=42.0,
            confidence=TAConfidence.from_score(0.95),
        )


def test_standard_timeframes_has_9_entries():
    """9 standard timeframes (Monthly to 1M)."""
    assert len(STANDARD_TIMEFRAMES) == 9
    assert Timeframe.MONTHLY in STANDARD_TIMEFRAMES
    assert Timeframe.ONE_MIN in STANDARD_TIMEFRAMES


def test_timeframe_context_contains():
    ctx = TimeframeContext()
    assert ctx.contains(Timeframe.DAILY)
    assert ctx.count == 9


def test_ta_confidence_from_score():
    """Confidence is derived from score."""
    assert TAConfidence.from_score(0.999).quality == "A+"
    assert TAConfidence.from_score(0.97).quality == "A"
    assert TAConfidence.from_score(0.85).quality == "B"
    assert TAConfidence.from_score(0.65).quality == "C"
    assert TAConfidence.from_score(0.45).quality == "D"
    assert TAConfidence.from_score(0.15).quality == "F"


def test_ta_output_to_event_payload():
    """TAOutput converts to event payload."""
    output = TAOutput(
        agent="EMA", symbol="SPY", timeframe="15m",
        indicator="EMA20", value=450.0,
        confidence=TAConfidence(score=0.99, quality="A+"),
    )
    payload = output.to_event_payload()
    assert payload["agent"] == "EMA"
    assert payload["symbol"] == "SPY"
    assert payload["value"] == 450.0
    assert payload["confidence"] == 0.99
    assert payload["quality"] == "A+"


async def test_base_agent_compute_and_publish():
    """BaseTAAgent.compute_and_publish emits event."""
    from athena_x_runtime_event_bus import InMemoryBusClient

    bus = InMemoryBusClient()
    agent = FakeTAAgent()

    received = []
    async def handler(event):
        received.append(event)
    await bus.subscribe("ai:technical:*", handler)

    output = await agent.compute_and_publish("SPY", Timeframe.FIFTEEN_MIN, repo=None, event_bus=bus)

    assert output.value == 42.0
    assert len(received) >= 1
    await bus.close()


def test_base_agent_health():
    """get_health returns agent status."""
    agent = FakeTAAgent()
    health = agent.get_health()
    assert health["name"] == "fake"
    assert health["layer"] == 2
    assert health["calculation_count"] == 0


def test_bar_cache_hits_and_misses():
    """Bar cache tracks hits + misses."""
    cache = BarCache()
    assert cache.get_stats()["hit_rate"] == 0.0


def test_cached_bars_properties():
    """CachedBars exposes OHLCV lists."""
    bars = CachedBars(
        symbol="SPY", timeframe="15m",
        bars=[
            {"open": 100, "high": 101, "low": 99, "close": 100.5, "volume": 1000},
            {"open": 100.5, "high": 102, "low": 100, "close": 101.5, "volume": 2000},
        ],
    )
    assert bars.closes == [100.5, 101.5]
    assert bars.opens == [100, 100.5]
    assert bars.highs == [101, 102]
    assert bars.lows == [99, 100]
    assert bars.volumes == [1000, 2000]
    assert not bars.is_stale  # just created
