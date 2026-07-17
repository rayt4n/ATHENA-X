"""Tests for Market DNA Agent."""
import pytest
from athena_x_agent_market_intelligence import MarketDNA, MarketDNAAgent, MarketIntelligenceHub


@pytest.fixture
def quotes():
    return {
        "SPY": {"last": 450.0, "change_pct": 0.5},
        "ES": {"last": 4520.0, "change_pct": 0.4},
        "VIX": {"last": 15.0, "change_pct": -2.0},
        "TNX": {"last": 4.3, "change_pct": 0.1},
        "DXY": {"last": 100.5, "change_pct": -0.1},
        "XLK": {"last": 180.0, "change_pct": 0.8},
        "XLU": {"last": 65.0, "change_pct": -0.2},
        "SOXX": {"last": 200.0, "change_pct": 1.2},
    }


@pytest.fixture
def returns():
    return {
        "SPY": [0.001, 0.002, -0.001, 0.003, 0.001, 0.002, 0.001, 0.002, 0.001, 0.003],
        "ES": [0.001, 0.002, -0.001, 0.003, 0.001, 0.002, 0.001, 0.002, 0.001, 0.003],
        "VIX": [-0.01, -0.02, 0.01, -0.03, -0.01, -0.02, -0.01, -0.02, -0.01, -0.03],
        "DXY": [-0.001, -0.002, 0.001, -0.003, -0.001, -0.002, -0.001, -0.002, -0.001, -0.003],
        "TNX": [0.001, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001],
        "XLK": [0.002, 0.003, 0.001, 0.004, 0.002, 0.003, 0.002, 0.003, 0.002, 0.004],
        "XLU": [-0.001, -0.001, 0.001, -0.002, -0.001, -0.001, 0.001, -0.002, -0.001, -0.001],
        "SOXX": [0.003, 0.004, 0.002, 0.005, 0.003, 0.004, 0.003, 0.004, 0.003, 0.005],
    }


async def test_dna_includes_regime(quotes, returns):
    """Market DNA includes regime classification."""
    agent = MarketDNAAgent()
    dna = await agent.compute_dna(quotes, returns)
    assert dna.market_regime in ("Risk-On", "Risk-Off", "Neutral")


async def test_dna_includes_trend(quotes, returns):
    """Market DNA includes trend."""
    agent = MarketDNAAgent()
    dna = await agent.compute_dna(quotes, returns)
    assert dna.trend in ("Bullish", "Bearish", "Ranging")


async def test_dna_includes_volatility(quotes, returns):
    """Market DNA includes volatility regime."""
    agent = MarketDNAAgent()
    dna = await agent.compute_dna(quotes, returns)
    assert dna.volatility in ("Expanding", "Contracting", "Normal")


async def test_dna_includes_leadership(quotes, returns):
    """Market DNA includes sector leadership."""
    agent = MarketDNAAgent()
    dna = await agent.compute_dna(quotes, returns)
    assert dna.leadership is not None


async def test_dna_includes_strongest_weakest(quotes, returns):
    """Market DNA includes strongest and weakest assets."""
    agent = MarketDNAAgent()
    dna = await agent.compute_dna(quotes, returns)
    assert dna.strongest_asset is not None
    assert dna.weakest_asset is not None


async def test_dna_includes_risk_score(quotes, returns):
    """Market DNA includes risk score 0-100."""
    agent = MarketDNAAgent()
    dna = await agent.compute_dna(quotes, returns)
    assert 0 <= dna.risk_score <= 100


async def test_dna_includes_correlations(quotes, returns):
    """Market DNA includes key correlations."""
    agent = MarketDNAAgent()
    dna = await agent.compute_dna(quotes, returns)
    assert dna.spy_es_correlation is not None
    assert dna.spy_vix_correlation is not None


async def test_dna_includes_confidence(quotes, returns):
    """Market DNA includes confidence."""
    agent = MarketDNAAgent()
    dna = await agent.compute_dna(quotes, returns)
    assert 0 < dna.confidence <= 1.0


async def test_dna_event_published(quotes, returns):
    """Market DNA publishes market:dna_updated event."""
    from athena_x_runtime_event_bus import InMemoryBusClient

    bus = InMemoryBusClient()
    agent = MarketDNAAgent(event_bus=bus)

    received = []
    async def handler(event):
        received.append(event)
    await bus.subscribe("market:dna_updated", handler)

    await agent.compute_dna(quotes, returns)

    assert len(received) == 1
    assert "market_regime" in received[0].payload
    await bus.close()


def test_hub_collects_quotes():
    """Market Intelligence Hub collects and stores quotes."""
    hub = MarketIntelligenceHub()
    hub.update_quote("SPY", {"last": 450.0})
    hub.update_quote("ES", {"last": 4520.0})
    quotes = hub.get_quotes()
    assert "SPY" in quotes
    assert "ES" in quotes


def test_hub_snapshot():
    """Hub produces synchronized snapshots."""
    hub = MarketIntelligenceHub()
    hub.update_quote("SPY", {"last": 450.0})
    snapshot = hub.get_snapshot()
    assert "timestamp" in snapshot
    assert "quotes" in snapshot
    assert snapshot["symbols_tracked"] == 1


def test_hub_adds_signals():
    """Hub collects cross-market signals."""
    hub = MarketIntelligenceHub()
    hub.add_signal({"type": "divergence", "description": "VIX not confirming"})
    snapshot = hub.get_snapshot()
    assert len(snapshot["recent_signals"]) == 1
