"""Tests for simulated provider."""
import pytest
from athena_x_provider_simulated import SimulatedAdapter


@pytest.fixture
async def provider():
    p = SimulatedAdapter(seed=42)
    yield p


async def test_fetch_quote_returns_valid_data(provider):
    result = await provider.fetch_quote("NVDA")
    assert result.provider == "simulated"
    assert result.data["symbol"] == "NVDA"
    assert result.data["last"] > 0
    assert "bid" in result.data
    assert "ask" in result.data
    assert result.latency_ms >= 0


async def test_quote_random_walk_changes_price(provider):
    """Successive quotes have different prices (random walk)."""
    r1 = await provider.fetch_quote("SPY")
    r2 = await provider.fetch_quote("SPY")
    assert r1.data["last"] != r2.data["last"]


async def test_deterministic_with_same_seed():
    """Same seed produces same sequence of quotes."""
    p1 = SimulatedAdapter(seed=123)
    p2 = SimulatedAdapter(seed=123)
    r1 = await p1.fetch_quote("SPY")
    r2 = await p2.fetch_quote("SPY")
    assert r1.data["last"] == r2.data["last"]


async def test_fetch_bars(provider):
    results = await provider.fetch_quote("SPY")  # warm up
    bars = await provider.fetch_bars("SPY", "1m", 10)
    assert len(bars) == 10
    for result in bars:
        assert result.data["symbol"] == "SPY"
        assert result.data["open"] > 0
        assert result.data["high"] >= result.data["open"]
        assert result.data["low"] <= result.data["open"]
        assert result.provider == "simulated"


async def test_health_check(provider):
    await provider.fetch_quote("SPY")
    health = await provider.health_check()
    assert health["provider"] == "simulated"
    assert health["connection"] == "connected"
    assert health["reliabilityScore"] == 1.0


async def test_unknown_symbol_uses_default_price(provider):
    """Unknown symbols start at $100."""
    result = await provider.fetch_quote("UNKNOWN")
    assert 90 < result.data["last"] < 110  # near default $100 after small walk
