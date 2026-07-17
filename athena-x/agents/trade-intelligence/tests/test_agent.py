"""Tests for Trade DNA Agent."""
import pytest
from athena_x_agent_trade_intelligence import TradeDNAAgent
from athena_x_engine_trade_engine import TradeStatus


@pytest.fixture
def agent():
    return TradeDNAAgent()


@pytest.fixture
def dna_objects():
    """All 5 DNA objects."""
    return {
        "technical_dna": {
            "trend": "bullish", "rsi": 45, "ema": 450, "atr": 2.0,
            "alignment_score": 82, "wyckoff_phase": "accumulation",
        },
        "options_dna": {
            "dealer_gamma": "long", "iv_regime": "low",
            "expected_move": 5.2, "iv_crush_risk": 0.2, "intraday_risk": "low",
        },
        "market_dna": {
            "market_regime": "Risk-On", "breadth": "Strong",
            "risk_score": 25, "leadership": "SOXX",
            "spy_es_correlation": 0.98, "spy_vix_correlation": -0.7,
        },
        "narrative_dna": {
            "primary_driver": "Fed dovish", "confidence": 0.85,
            "upcoming_catalysts": [],
        },
        "forecast_dna": {
            "direction": "bullish", "target_price": 458,
            "confidence": 0.85, "model_agreement": 0.88,
            "bull": {"probability": 0.58},
            "bear": {"probability": 0.14},
            "base": {"probability": 0.28},
        },
    }


async def test_trade_dna_produced(agent, dna_objects):
    """Trade DNA Agent produces TradeDNA."""
    dna = await agent.compute_trade_dna(symbol="SPY", **dna_objects)
    assert dna.symbol == "SPY"
    assert dna.trade_status in list(TradeStatus)


async def test_trade_dna_includes_readiness_meter(agent, dna_objects):
    """Trade DNA includes Readiness Meter (0-100)."""
    dna = await agent.compute_trade_dna(symbol="SPY", **dna_objects)
    assert 0 <= dna.readiness_meter.score <= 100
    assert dna.readiness_meter.label in ("Stand Aside", "Monitor", "Prepare", "High Probability Setup", "Institutional-Grade Opportunity")


async def test_trade_dna_includes_alignment(agent, dna_objects):
    """Trade DNA includes alignment of 5 DNA objects."""
    dna = await agent.compute_trade_dna(symbol="SPY", **dna_objects)
    assert dna.alignment.technical is True
    assert dna.alignment.options is True
    assert dna.alignment.market is True
    assert dna.alignment.narrative is True
    assert dna.alignment.forecast is True
    assert dna.alignment_score == 1.0


async def test_trade_dna_includes_checklist(agent, dna_objects):
    """Trade DNA includes institutional checklist."""
    dna = await agent.compute_trade_dna(symbol="SPY", **dna_objects)
    assert dna.checklist.total == 10
    assert dna.checklist.passed_count > 5


async def test_trade_dna_includes_scenarios(agent, dna_objects):
    """Trade DNA includes bull/bear/neutral scenarios."""
    dna = await agent.compute_trade_dna(symbol="SPY", **dna_objects)
    assert dna.bull_plan.direction == "bull"
    assert dna.bear_plan.direction == "bear"
    assert dna.neutral_plan.direction == "neutral"


async def test_trade_dna_includes_option_timing(agent, dna_objects):
    """Trade DNA includes option timing assessment."""
    dna = await agent.compute_trade_dna(symbol="SPY", **dna_objects)
    assert dna.option_timing.best_strategy != ""
    assert dna.option_timing.suggested_holding != ""


async def test_trade_dna_includes_drivers_and_threats(agent, dna_objects):
    """Trade DNA includes drivers and threats."""
    dna = await agent.compute_trade_dna(symbol="SPY", **dna_objects)
    assert len(dna.drivers) > 0
    assert isinstance(dna.threats, list)


async def test_trade_dna_includes_explanation(agent, dna_objects):
    """Trade DNA includes human-readable explanation."""
    dna = await agent.compute_trade_dna(symbol="SPY", **dna_objects)
    assert len(dna.explanation) > 0
    assert "Trade Status" in dna.explanation


async def test_trade_dna_includes_opportunity_ranking(agent, dna_objects):
    """Trade DNA includes ranked opportunities."""
    dna = await agent.compute_trade_dna(symbol="SPY", **dna_objects)
    assert len(dna.opportunities) >= 2
    assert dna.opportunities[0].rank == 1


async def test_trade_dna_event_published(agent, dna_objects):
    """Trade DNA publishes ai:trade:dna event."""
    from athena_x_runtime_event_bus import InMemoryBusClient

    bus = InMemoryBusClient()
    agent._bus = bus

    received = []
    async def handler(event):
        received.append(event)
    await bus.subscribe("ai:trade:dna", handler)

    await agent.compute_trade_dna(symbol="SPY", **dna_objects)

    assert len(received) == 1
    assert "trade_status" in received[0].payload
    await bus.close()


async def test_trade_dna_no_trade_when_poor_conditions(agent):
    """Trade DNA says NO_TRADE when conditions are poor."""
    dna = await agent.compute_trade_dna(
        symbol="SPY",
        technical_dna={"trend": "unknown"},
        options_dna={"dealer_gamma": "unknown"},
        market_dna={"market_regime": "unknown", "risk_score": 85},
        narrative_dna={"primary_driver": "unknown"},
        forecast_dna={"direction": "neutral"},
    )
    assert dna.trade_status == TradeStatus.NO_TRADE
    assert dna.readiness_meter.score <= 50


async def test_6th_intelligence_object(agent, dna_objects):
    """Trade DNA is the 6th intelligence object."""
    dna = await agent.compute_trade_dna(symbol="SPY", **dna_objects)
    # Has all fields for downstream consumption
    assert hasattr(dna, "trade_status")
    assert hasattr(dna, "readiness_meter")
    assert hasattr(dna, "alignment")
    assert hasattr(dna, "entry_quality")
    assert hasattr(dna, "option_timing")
    assert hasattr(dna, "risk")
    assert hasattr(dna, "checklist")
    assert hasattr(dna, "bull_plan")
    assert hasattr(dna, "bear_plan")
    assert hasattr(dna, "neutral_plan")
    assert hasattr(dna, "opportunities")
    assert hasattr(dna, "explanation")
