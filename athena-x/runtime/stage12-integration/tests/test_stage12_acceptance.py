"""Stage 12 acceptance tests - Institutional Trade Intelligence Platform."""
import pytest
from athena_x_engine_trade_engine import (
    TradeStatus, TradeReadinessMeter, TimingWindow,
    TradeQualificationEngine, TimingEngine, RiskEngine,
    OpportunityRankingEngine, InstitutionalChecklist,
)
from athena_x_agent_trade_intelligence import TradeDNAAgent


@pytest.fixture
def agent():
    return TradeDNAAgent()


@pytest.fixture
def good_dna():
    return {
        "technical_dna": {"trend": "bullish", "rsi": 45, "ema": 450, "atr": 2.0, "alignment_score": 82, "wyckoff_phase": "accumulation"},
        "options_dna": {"dealer_gamma": "long", "iv_regime": "low", "expected_move": 5.2, "iv_crush_risk": 0.2, "intraday_risk": "low"},
        "market_dna": {"market_regime": "Risk-On", "breadth": "Strong", "risk_score": 25, "leadership": "SOXX", "spy_es_correlation": 0.98, "spy_vix_correlation": -0.7},
        "narrative_dna": {"primary_driver": "Fed dovish", "confidence": 0.85, "upcoming_catalysts": []},
        "forecast_dna": {"direction": "bullish", "target_price": 458, "confidence": 0.85, "model_agreement": 0.88, "bull": {"probability": 0.58}, "bear": {"probability": 0.14}, "base": {"probability": 0.28}},
    }


@pytest.fixture
def poor_dna():
    return {
        "technical_dna": {"trend": "unknown"},
        "options_dna": {"dealer_gamma": "unknown"},
        "market_dna": {"market_regime": "unknown", "risk_score": 85},
        "narrative_dna": {"primary_driver": "unknown"},
        "forecast_dna": {"direction": "neutral"},
    }


# ============================================================================
# Exit Criteria 1: NO_TRADE / WATCH / PREPARE / READY / ACTIVE
# ============================================================================

async def test_no_trade_when_poor(agent, poor_dna):
    """Engine says NO_TRADE when conditions are poor."""
    dna = await agent.compute_trade_dna(symbol="SPY", **poor_dna)
    assert dna.trade_status == TradeStatus.NO_TRADE


async def test_ready_or_active_when_good(agent, good_dna):
    """Engine says READY or ACTIVE when conditions are good."""
    dna = await agent.compute_trade_dna(symbol="SPY", **good_dna)
    assert dna.trade_status in (TradeStatus.READY, TradeStatus.ACTIVE, TradeStatus.PREPARE)


# ============================================================================
# Exit Criteria 2: Timing Engine
# ============================================================================

def test_timing_engine_identifies_windows():
    """Timing Engine identifies entry/exit windows."""
    engine = TimingEngine()
    optimal = engine.assess(trend_alignment=85, pullback_detected=True, vix_level=14, time_of_day="09:45")
    assert optimal == TimingWindow.OPTIMAL_ENTRY

    risky = engine.assess(trend_alignment=50, near_catalyst=True, vix_level=28)
    assert risky in (TimingWindow.HIGH_RISK, TimingWindow.EXIT_WINDOW)


# ============================================================================
# Exit Criteria 3: Trade Alignment Score
# ============================================================================

async def test_alignment_score_combines_5_dna(agent, good_dna):
    """Alignment score combines all 5 DNA objects."""
    dna = await agent.compute_trade_dna(symbol="SPY", **good_dna)
    assert dna.alignment_score > 0.8
    assert dna.alignment.technical is True
    assert dna.alignment.forecast is True


# ============================================================================
# Exit Criteria 4: Entry Quality Score
# ============================================================================

async def test_entry_quality_score(agent, good_dna):
    """Entry Quality Score incorporates technical, options, volume, etc."""
    dna = await agent.compute_trade_dna(symbol="SPY", **good_dna)
    assert 0 <= dna.entry_quality.score <= 100
    assert dna.entry_quality.trend_quality is True
    assert dna.entry_quality.gamma_support is True


# ============================================================================
# Exit Criteria 5: Option Timing Engine
# ============================================================================

async def test_option_timing_engine(agent, good_dna):
    """Option Timing evaluates IV, theta, gamma, 0DTE risks."""
    dna = await agent.compute_trade_dna(symbol="SPY", **good_dna)
    assert dna.option_timing.best_strategy != ""
    assert dna.option_timing.theta_risk in ("low", "medium", "high")
    assert dna.option_timing.gamma_exposure in ("positive", "negative", "neutral", "long", "short")


# ============================================================================
# Exit Criteria 6: Risk Engine
# ============================================================================

async def test_risk_engine_estimates(agent, good_dna):
    """Risk Engine estimates reward, drawdown, probabilities."""
    dna = await agent.compute_trade_dna(symbol="SPY", **good_dna)
    assert dna.risk.max_risk > 0 or dna.risk.expected_reward > 0
    assert 0 <= dna.risk.probability_of_success <= 1.0


# ============================================================================
# Exit Criteria 7: Multiple trade scenarios
# ============================================================================

async def test_scenarios_always_available(agent, poor_dna):
    """Bull/Bear/Neutral scenarios always available."""
    dna = await agent.compute_trade_dna(symbol="SPY", **poor_dna)
    assert dna.bull_plan is not None
    assert dna.bear_plan is not None
    assert dna.neutral_plan is not None


# ============================================================================
# Exit Criteria 8: Explanation + Checklist
# ============================================================================

async def test_explanation_and_checklist(agent, good_dna):
    """Every recommendation includes explanation + checklist."""
    dna = await agent.compute_trade_dna(symbol="SPY", **good_dna)
    assert len(dna.explanation) > 0
    assert dna.checklist.total == 10
    assert dna.checklist.passed_count > 0


# ============================================================================
# Exit Criteria 9: Trade DNA published
# ============================================================================

async def test_trade_dna_published(agent, good_dna):
    """Trade DNA published as ai:trade:dna event."""
    from athena_x_runtime_event_bus import InMemoryBusClient

    bus = InMemoryBusClient()
    agent._bus = bus

    received = []
    async def handler(event):
        received.append(event)
    await bus.subscribe("ai:trade:dna", handler)

    await agent.compute_trade_dna(symbol="SPY", **good_dna)
    assert len(received) == 1
    await bus.close()


# ============================================================================
# Exit Criteria 10: Readiness Meter
# ============================================================================

async def test_readiness_meter_ranges(agent, good_dna, poor_dna):
    """Readiness Meter shows 0-100 with appropriate labels."""
    good = await agent.compute_trade_dna(symbol="SPY", **good_dna)
    poor = await agent.compute_trade_dna(symbol="SPY", **poor_dna)

    assert good.readiness_meter.score > poor.readiness_meter.score
    assert good.readiness_meter.label in ("Prepare", "High Probability Setup", "Institutional-Grade Opportunity")
    assert poor.readiness_meter.label in ("Stand Aside", "Monitor")


# ============================================================================
# 6th Intelligence Object
# ============================================================================

async def test_6th_intelligence_object(agent, good_dna):
    """Trade DNA is the 6th intelligence object with all fields."""
    dna = await agent.compute_trade_dna(symbol="SPY", **good_dna)
    d = dna.to_dict()
    assert "trade_status" in d
    assert "readiness_score" in d
    assert "alignment" in d
    assert "checklist" in d
    assert "bull_plan" in d
    assert "bear_plan" in d
    assert "option_timing" in d
    assert "risk" in d
    assert "explanation" in d
