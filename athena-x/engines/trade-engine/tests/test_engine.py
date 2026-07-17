"""Tests for Trade Engine."""
import pytest
from athena_x_engine_trade_engine import (
    TradeDNA, TradeStatus, TradeReadinessMeter,
    TimingWindow, RiskAssessment, TradeAlignment,
    EntryQuality, OptionTiming, TradeScenario,
    InstitutionalChecklist, TradeRanking,
    TradeQualificationEngine, TimingEngine,
    RiskEngine, OpportunityRankingEngine,
)


# ============================================================================
# Trade Qualification tests
# ============================================================================

def test_qualification_no_trade_high_risk():
    """High risk = NO_TRADE."""
    engine = TradeQualificationEngine()
    status = engine.qualify(
        alignment=TradeAlignment(technical=True, options=True, market=True, narrative=True, forecast=True),
        risk_score=85,
        timing_score=80,
    )
    assert status == TradeStatus.NO_TRADE


def test_qualification_no_trade_low_alignment():
    """Low alignment = NO_TRADE."""
    engine = TradeQualificationEngine()
    status = engine.qualify(
        alignment=TradeAlignment(technical=True, options=False, market=False, narrative=False, forecast=False),
        risk_score=30,
        timing_score=70,
    )
    assert status == TradeStatus.NO_TRADE


def test_qualification_watch_partial_alignment():
    """Partial alignment = WATCH."""
    engine = TradeQualificationEngine()
    status = engine.qualify(
        alignment=TradeAlignment(technical=True, options=True, market=False, narrative=False, forecast=False),
        risk_score=30,
        timing_score=50,
    )
    assert status == TradeStatus.WATCH


def test_qualification_ready():
    """Good alignment + timing = READY."""
    engine = TradeQualificationEngine()
    status = engine.qualify(
        alignment=TradeAlignment(technical=True, options=True, market=True, narrative=True, forecast=True),
        risk_score=30,
        timing_score=65,
        entry_quality=65,
    )
    assert status == TradeStatus.READY


def test_qualification_active():
    """Excellent conditions = ACTIVE."""
    engine = TradeQualificationEngine()
    status = engine.qualify(
        alignment=TradeAlignment(technical=True, options=True, market=True, narrative=True, forecast=True),
        risk_score=25,
        timing_score=80,
        entry_quality=75,
    )
    assert status == TradeStatus.ACTIVE


# ============================================================================
# Timing Engine tests
# ============================================================================

def test_timing_optimal_entry():
    """Good conditions = OPTIMAL_ENTRY."""
    engine = TimingEngine()
    timing = engine.assess(
        trend_alignment=85,
        pullback_detected=True,
        distance_from_support=0.2,
        vix_level=14,
        time_of_day="09:45",
    )
    assert timing == TimingWindow.OPTIMAL_ENTRY


def test_timing_high_risk_near_catalyst():
    """Near catalyst = HIGH_RISK or worse."""
    engine = TimingEngine()
    timing = engine.assess(
        trend_alignment=50,
        near_catalyst=True,
        vix_level=28,
    )
    assert timing in (TimingWindow.HIGH_RISK, TimingWindow.EXIT_WINDOW)


def test_timing_too_early():
    """No pullback = TOO_EARLY."""
    engine = TimingEngine()
    timing = engine.assess(
        trend_alignment=70,
        pullback_detected=False,
        distance_from_resistance=0.1,
    )
    assert timing in (TimingWindow.TOO_EARLY, TimingWindow.CHASING)


# ============================================================================
# Risk Engine tests
# ============================================================================

def test_risk_engine_computes_metrics():
    """Risk engine computes risk/reward."""
    engine = RiskEngine()
    risk = engine.assess(
        entry=455,
        stop=453,
        target=458,
        probability_of_success=0.65,
        atr=1.5,
    )
    assert risk.max_risk == 2.0
    assert risk.expected_reward == 3.0
    assert risk.risk_reward_ratio == 1.5
    assert risk.probability_of_success == 0.65


# ============================================================================
# Opportunity Ranking tests
# ============================================================================

def test_ranking_sorts_by_score():
    """Ranking engine sorts by score (highest first)."""
    engine = OpportunityRankingEngine()
    rankings = engine.rank([
        TradeRanking(symbol="QQQ", trade_type="Calls", score=84),
        TradeRanking(symbol="SPY", trade_type="Calls", score=94),
        TradeRanking(symbol="ES", trade_type="Long", score=90),
    ])
    assert rankings[0].symbol == "SPY"
    assert rankings[0].rank == 1
    assert rankings[1].symbol == "ES"
    assert rankings[1].rank == 2


# ============================================================================
# Trade Readiness Meter tests
# ============================================================================

def test_readiness_meter_stand_aside():
    meter = TradeReadinessMeter(score=25)
    assert meter.label == "Stand Aside"


def test_readiness_meter_monitor():
    meter = TradeReadinessMeter(score=40)
    assert meter.label == "Monitor"


def test_readiness_meter_prepare():
    meter = TradeReadinessMeter(score=60)
    assert meter.label == "Prepare"


def test_readiness_meter_high_probability():
    meter = TradeReadinessMeter(score=78)
    assert meter.label == "High Probability Setup"


def test_readiness_meter_institutional():
    meter = TradeReadinessMeter(score=92)
    assert meter.label == "Institutional-Grade Opportunity"


# ============================================================================
# Trade DNA tests
# ============================================================================

def test_trade_dna_has_all_fields():
    dna = TradeDNA(symbol="SPY")
    assert dna.trade_status == TradeStatus.NO_TRADE
    assert dna.alignment is not None
    assert dna.checklist is not None
    assert dna.readiness_meter is not None
    assert dna.bull_plan is not None
    assert dna.bear_plan is not None
    assert dna.neutral_plan is not None


def test_trade_dna_serializable():
    dna = TradeDNA(symbol="ES", trade_status=TradeStatus.READY)
    d = dna.to_dict()
    assert d["symbol"] == "ES"
    assert d["trade_status"] == "READY"
    assert "alignment" in d
    assert "checklist" in d
    assert "readiness_label" in d


def test_checklist_pass_rate():
    checklist = InstitutionalChecklist(
        trend=True, multi_timeframe=True, volume=True,
        gamma=True, dealer=True, breadth=False,
        news=True, forecast=True, correlation=True, risk=False,
    )
    assert checklist.passed_count == 8
    assert checklist.pass_rate == 0.8


def test_alignment_score():
    align = TradeAlignment(technical=True, options=True, market=True, narrative=False, forecast=True)
    assert align.score == 0.8
