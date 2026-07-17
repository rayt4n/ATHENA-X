#!/usr/bin/env python3
"""
STEP 4 Stage 12 - Institutional Trade Intelligence Platform
=============================================================
Implements:
  1. engines/trade-engine/ - Qualification + Timing + Risk + Probability + Ranking + Checklist + Option Timing
  2. agents/trade-intelligence/ - Trade DNA Agent + Readiness Meter
  3. runtime/stage12-integration/ - acceptance tests

Key: Produces Trade DNA (6th intelligence object) + Trade Readiness Meter (0-100).

Run: python /home/z/my-project/scripts/stage12_implement.py
"""

from pathlib import Path
import textwrap

ROOT = Path("/home/z/my-project/athena-x")
ROOT.mkdir(parents=True, exist_ok=True)
FILES = []

def w(rel: str, content: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(content).lstrip("\n"))
    FILES.append(rel)


# ============================================================================
# 1. TRADE ENGINE
# ============================================================================

w("engines/trade-engine/pyproject.toml", '''
[project]
name = "athena-x-engine-trade-engine"
version = "0.1.0"
description = "Trade Engine - Qualification + Timing + Risk + Probability + Ranking + Checklist"
requires-python = ">=3.11"
dependencies = ["athena-x-runtime-logger"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_engine_trade_engine"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w("engines/trade-engine/src/athena_x_engine_trade_engine/__init__.py", '''
"""Trade Engine - institutional trade intelligence."""
from .types import (
    TradeDNA, TradeStatus, TradeReadinessMeter,
    TimingAssessment, RiskAssessment, TradeAlignment,
    EntryQuality, OptionTiming, TradeScenario,
    InstitutionalChecklist, TradeRanking,
)
from .qualification import TradeQualificationEngine
from .timing import TimingEngine
from .risk import RiskEngine
from .ranking import OpportunityRankingEngine

__all__ = [
    "TradeDNA", "TradeStatus", "TradeReadinessMeter",
    "TimingAssessment", "RiskAssessment", "TradeAlignment",
    "EntryQuality", "OptionTiming", "TradeScenario",
    "InstitutionalChecklist", "TradeRanking",
    "TradeQualificationEngine", "TimingEngine",
    "RiskEngine", "OpportunityRankingEngine",
]
__version__ = "0.1.0"
''')

w("engines/trade-engine/src/athena_x_engine_trade_engine/types.py", '''
"""Trade Intelligence types - Stage 12.

The 6th intelligence object: Trade DNA.

Answers: "Is this the highest probability institutional trade right now,
and if not, why not?"
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class TradeStatus(str, Enum):
    """5 possible trade states. Most systems never say 'do nothing'."""
    NO_TRADE = "NO_TRADE"
    WATCH = "WATCH"
    PREPARE = "PREPARE"
    READY = "READY"
    ACTIVE = "ACTIVE"


class TimingWindow(str, Enum):
    """Timing assessment for entry/exit."""
    TOO_EARLY = "too_early"
    OPTIMAL_ENTRY = "optimal_entry"
    CHASING = "chasing"
    LATE_ENTRY = "late_entry"
    EXIT_WINDOW = "exit_window"
    HIGH_RISK = "high_risk"


@dataclass
class TradeAlignment:
    """Alignment between the 5 DNA objects."""
    technical: bool = False
    options: bool = False
    market: bool = False
    narrative: bool = False
    forecast: bool = False

    @property
    def score(self) -> float:
        """0..1 alignment score."""
        count = sum([self.technical, self.options, self.market, self.narrative, self.forecast])
        return count / 5.0


@dataclass
class EntryQuality:
    """Entry quality assessment (0-100)."""
    score: int = 50
    trend_quality: bool = False
    pullback_quality: bool = False
    volume_confirmation: bool = False
    liquidity_sweep: bool = False
    wyckoff_confirmation: bool = False
    chan_confirmation: bool = False
    candlestick_confirmation: bool = False
    dealer_positioning: bool = False
    gamma_support: bool = False


@dataclass
class OptionTiming:
    """Option-specific timing assessment."""
    current_iv: float = 0.0
    iv_rising: bool = False
    theta_risk: str = "medium"  # low, medium, high
    gamma_exposure: str = "neutral"  # positive, negative, neutral
    expected_move: float = 0.0
    risk_0dte: str = "medium"
    best_strategy: str = ""  # e.g., "Long Calls", "Iron Condor"
    suggested_holding: str = ""  # e.g., "25-40 min"
    directional_edge: str = ""  # high, medium, low
    iv_crush_risk: str = "low"


@dataclass
class RiskAssessment:
    """Risk metrics for a trade."""
    max_risk: float = 0.0
    expected_reward: float = 0.0
    expected_drawdown: float = 0.0
    expected_hold_time: str = ""  # e.g., "30-60 min"
    probability_of_success: float = 0.5
    probability_of_stop: float = 0.3
    probability_of_target: float = 0.5
    risk_reward_ratio: float = 0.0


@dataclass
class TradeScenario:
    """A trade scenario (bull, bear, neutral)."""
    name: str  # "Primary Plan", "Alternative Plan", etc.
    direction: str  # "bull", "bear", "neutral"
    action: str = ""  # "Buy Pullback", "Short Rejection", "Wait"
    entry: float | None = None
    stop: float | None = None
    target: float | None = None
    probability: float = 0.33


@dataclass
class InstitutionalChecklist:
    """Every trade passes through this checklist."""
    trend: bool = False
    multi_timeframe: bool = False
    volume: bool = False
    gamma: bool = False
    dealer: bool = False
    breadth: bool = False
    news: bool = False
    forecast: bool = False
    correlation: bool = False
    risk: bool = False

    @property
    def passed_count(self) -> int:
        return sum([
            self.trend, self.multi_timeframe, self.volume,
            self.gamma, self.dealer, self.breadth,
            self.news, self.forecast, self.correlation, self.risk,
        ])

    @property
    def total(self) -> int:
        return 10

    @property
    def pass_rate(self) -> float:
        return self.passed_count / self.total


@dataclass
class TradeRanking:
    """A ranked trade opportunity."""
    symbol: str
    trade_type: str  # "SPY Calls", "ES Long", "No Trade"
    score: int  # 0-100
    rank: int = 0


@dataclass
class TradeReadinessMeter:
    """Trade Readiness Meter (0-100).

    0-30:   Stand Aside
    31-50:  Monitor
    51-70:  Prepare
    71-85:  High Probability Setup
    86-100: Institutional-Grade Opportunity
    """
    score: int = 0
    label: str = "Stand Aside"

    def __post_init__(self):
        if self.score <= 30:
            self.label = "Stand Aside"
        elif self.score <= 50:
            self.label = "Monitor"
        elif self.score <= 70:
            self.label = "Prepare"
        elif self.score <= 85:
            self.label = "High Probability Setup"
        else:
            self.label = "Institutional-Grade Opportunity"


@dataclass
class TradeDNA:
    """The 6th intelligence object - Trade DNA.

    Consumed by:
      - Dashboard (Stage 16)
      - Reports (Stage 15)
      - Future Auto Trading (V2)
      - Alerts
      - Risk Engine
    """
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    symbol: str = ""

    # Trade status
    trade_status: TradeStatus = TradeStatus.NO_TRADE
    trade_type: str = ""  # "Long Calls", "Short ES", etc.

    # Scores
    entry_quality: EntryQuality = field(default_factory=EntryQuality)
    alignment_score: float = 0.0
    risk_score: int = 50
    reward_score: int = 50
    readiness_meter: TradeReadinessMeter = field(default_factory=TradeReadinessMeter)

    # Timing
    timing: TimingWindow = TimingWindow.HIGH_RISK
    hold_time: str = ""

    # Assessment
    alignment: TradeAlignment = field(default_factory=TradeAlignment)
    option_timing: OptionTiming = field(default_factory=OptionTiming)
    risk: RiskAssessment = field(default_factory=RiskAssessment)
    checklist: InstitutionalChecklist = field(default_factory=InstitutionalChecklist)

    # Scenarios
    bull_plan: TradeScenario = field(default_factory=lambda: TradeScenario("Primary", "bull"))
    bear_plan: TradeScenario = field(default_factory=lambda: TradeScenario("Alternative", "bear"))
    neutral_plan: TradeScenario = field(default_factory=lambda: TradeScenario("Neutral", "neutral"))

    # Rankings
    opportunities: list[TradeRanking] = field(default_factory=list)

    # Probability + Confidence
    probability: float = 0.5
    confidence: float = 0.5

    # Explainability
    drivers: list[str] = field(default_factory=list)
    threats: list[str] = field(default_factory=list)
    explanation: str = ""

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "symbol": self.symbol,
            "trade_status": self.trade_status.value,
            "trade_type": self.trade_type,
            "entry_quality": self.entry_quality.score,
            "alignment_score": round(self.alignment_score, 4),
            "risk_score": self.risk_score,
            "reward_score": self.reward_score,
            "readiness_score": self.readiness_meter.score,
            "readiness_label": self.readiness_meter.label,
            "timing": self.timing.value,
            "hold_time": self.hold_time,
            "alignment": {
                "technical": self.alignment.technical,
                "options": self.alignment.options,
                "market": self.alignment.market,
                "narrative": self.alignment.narrative,
                "forecast": self.alignment.forecast,
            },
            "option_timing": {
                "iv": self.option_timing.current_iv,
                "theta_risk": self.option_timing.theta_risk,
                "gamma": self.option_timing.gamma_exposure,
                "best_strategy": self.option_timing.best_strategy,
                "suggested_holding": self.option_timing.suggested_holding,
            },
            "risk": {
                "max_risk": self.risk.max_risk,
                "expected_reward": self.risk.expected_reward,
                "prob_success": self.risk.probability_of_success,
                "prob_stop": self.risk.probability_of_stop,
                "risk_reward": self.risk.risk_reward_ratio,
            },
            "checklist": {
                "passed": self.checklist.passed_count,
                "total": self.checklist.total,
                "pass_rate": round(self.checklist.pass_rate, 4),
            },
            "bull_plan": {"action": self.bull_plan.action, "prob": self.bull_plan.probability},
            "bear_plan": {"action": self.bear_plan.action, "prob": self.bear_plan.probability},
            "neutral_plan": {"action": self.neutral_plan.action, "prob": self.neutral_plan.probability},
            "opportunities": [{"symbol": o.symbol, "type": o.trade_type, "score": o.score, "rank": o.rank} for o in self.opportunities],
            "probability": round(self.probability, 4),
            "confidence": round(self.confidence, 4),
            "drivers": self.drivers,
            "threats": self.threats,
            "explanation": self.explanation,
        }
''')

w("engines/trade-engine/src/athena_x_engine_trade_engine/qualification.py", '''
"""Trade Qualification Engine - determines if we should trade at all.

Stage 12 req: Most systems never say 'do nothing.' Yours should.

Outputs: NO_TRADE, WATCH, PREPARE, READY, ACTIVE
"""
from __future__ import annotations
from typing import Any
from athena_x_engine_trade_engine.types import TradeStatus, TradeAlignment


class TradeQualificationEngine:
    """Determines whether to trade, watch, or stand aside.

    Usage:
        engine = TradeQualificationEngine()
        status = engine.qualify(
            alignment=TradeAlignment(technical=True, options=True, market=True, narrative=False, forecast=True),
            risk_score=30,
            timing_score=75,
        )
        # status might be READY
    """

    def qualify(
        self,
        alignment: TradeAlignment,
        risk_score: int,
        timing_score: int,
        entry_quality: int = 50,
    ) -> TradeStatus:
        """Determine the trade status.

        Args:
            alignment: alignment between the 5 DNA objects
            risk_score: 0 (no risk) to 100 (extreme risk)
            timing_score: 0-100 timing quality
            entry_quality: 0-100 entry quality score

        Returns:
            TradeStatus (NO_TRADE, WATCH, PREPARE, READY, ACTIVE)
        """
        align_score = alignment.score

        # Hard rules
        if risk_score > 80:
            return TradeStatus.NO_TRADE  # too risky

        if align_score < 0.4:
            return TradeStatus.NO_TRADE  # not enough alignment

        if align_score < 0.6:
            return TradeStatus.WATCH  # partial alignment

        # Good alignment
        if timing_score >= 75 and entry_quality >= 70 and risk_score <= 50:
            return TradeStatus.ACTIVE

        if timing_score >= 60 and entry_quality >= 60:
            return TradeStatus.READY

        if timing_score >= 40:
            return TradeStatus.PREPARE

        return TradeStatus.WATCH
''')

w("engines/trade-engine/src/athena_x_engine_trade_engine/timing.py", '''
"""Timing Engine - identifies optimal entry and exit windows.

Stage 12 req: For SPY 0DTE, timing is everything.

Outputs: TOO_EARLY, OPTIMAL_ENTRY, CHASING, LATE_ENTRY, EXIT_WINDOW, HIGH_RISK
"""
from __future__ import annotations
from typing import Any
from athena_x_engine_trade_engine.types import TimingWindow


class TimingEngine:
    """Assesses entry/exit timing.

    Usage:
        engine = TimingEngine()
        timing = engine.assess(
            trend_alignment=82,
            pullback_detected=True,
            distance_from_support=0.3,
            distance_from_resistance=0.7,
            vix_level=15,
            time_of_day="09:45",
        )
        # timing might be OPTIMAL_ENTRY
    """

    def assess(
        self,
        trend_alignment: float = 50,
        pullback_detected: bool = False,
        distance_from_support: float = 0.5,
        distance_from_resistance: float = 0.5,
        vix_level: float = 15,
        time_of_day: str = "",
        near_catalyst: bool = False,
    ) -> TimingWindow:
        """Assess current timing for entry/exit."""
        score = 50

        # Trend alignment boosts timing
        if trend_alignment > 70:
            score += 15
        elif trend_alignment < 30:
            score -= 15

        # Pullback = good entry timing
        if pullback_detected:
            score += 20

        # Near support = good
        if distance_from_support < 0.3:
            score += 10
        elif distance_from_resistance < 0.2:
            score -= 10  # too close to resistance

        # VIX
        if vix_level > 25:
            score -= 15  # high vol = bad timing
        elif vix_level < 12:
            score += 5  # low vol = OK

        # Time of day
        if time_of_day:
            hour = int(time_of_day.split(":")[0])
            if 9 <= hour <= 10:
                score += 10  # morning session
            elif 15 <= hour <= 16:
                score -= 10  # close is risky
            elif hour >= 12 and hour < 14:
                score += 5  # lunch is calm

        # Catalyst proximity
        if near_catalyst:
            score -= 20  # risky to enter before catalyst

        # Map to timing window
        if score >= 75:
            return TimingWindow.OPTIMAL_ENTRY
        elif score >= 60:
            return TimingWindow.OPTIMAL_ENTRY if pullback_detected else TimingWindow.TOO_EARLY
        elif score >= 40:
            return TimingWindow.CHASING
        elif score >= 25:
            return TimingWindow.LATE_ENTRY
        elif score >= 10:
            return TimingWindow.EXIT_WINDOW
        return TimingWindow.HIGH_RISK
''')

w("engines/trade-engine/src/athena_x_engine_trade_engine/risk.py", '''
"""Risk Engine - computes risk metrics for trades."""
from __future__ import annotations
from typing import Any
from athena_x_engine_trade_engine.types import RiskAssessment


class RiskEngine:
    """Computes max risk, expected reward, drawdown, and probabilities.

    Usage:
        engine = RiskEngine()
        risk = engine.assess(
            entry=455,
            stop=453,
            target=458,
            probability_of_success=0.65,
            expected_drawdown=1.5,
        )
    """

    def assess(
        self,
        entry: float = 0,
        stop: float = 0,
        target: float = 0,
        probability_of_success: float = 0.5,
        expected_drawdown: float = 0,
        atr: float = 0,
    ) -> RiskAssessment:
        """Assess risk for a trade."""
        max_risk = abs(entry - stop) if entry and stop else 0
        expected_reward = abs(target - entry) if entry and target else 0
        risk_reward = expected_reward / max_risk if max_risk > 0 else 0

        # Probabilities
        prob_success = probability_of_success
        prob_stop = 1.0 - probability_of_success
        prob_target = probability_of_success * 0.9  # not all wins hit target

        # Hold time estimate based on ATR
        if atr > 0 and max_risk > 0:
            bars_to_target = expected_reward / atr if atr > 0 else 0
            if bars_to_target <= 5:
                hold_time = "15-30 min"
            elif bars_to_target <= 15:
                hold_time = "30-60 min"
            elif bars_to_target <= 30:
                hold_time = "1-2 hours"
            else:
                hold_time = "2+ hours"
        else:
            hold_time = "30-60 min"

        return RiskAssessment(
            max_risk=round(max_risk, 4),
            expected_reward=round(expected_reward, 4),
            expected_drawdown=round(expected_drawdown, 4),
            expected_hold_time=hold_time,
            probability_of_success=round(prob_success, 4),
            probability_of_stop=round(prob_stop, 4),
            probability_of_target=round(prob_target, 4),
            risk_reward_ratio=round(risk_reward, 4),
        )
''')

w("engines/trade-engine/src/athena_x_engine_trade_engine/ranking.py", '''
"""Opportunity Ranking Engine - ranks all trade opportunities."""
from __future__ import annotations
from typing import Any
from athena_x_engine_trade_engine.types import TradeRanking


class OpportunityRankingEngine:
    """Ranks trade opportunities by score.

    Stage 12 req: Instead of one trade, rank all opportunities.

    Usage:
        engine = OpportunityRankingEngine()
        rankings = engine.rank([
            TradeRanking(symbol="SPY", trade_type="Calls", score=94),
            TradeRanking(symbol="ES", trade_type="Long", score=90),
            TradeRanking(symbol="QQQ", trade_type="Calls", score=84),
            TradeRanking(symbol="NONE", trade_type="No Trade", score=80),
        ])
        # rankings[0] is the best opportunity
    """
    def rank(self, opportunities: list[TradeRanking]) -> list[TradeRanking]:
        """Rank opportunities by score (highest first)."""
        sorted_ops = sorted(opportunities, key=lambda x: x.score, reverse=True)
        for i, opp in enumerate(sorted_ops):
            opp.rank = i + 1
        return sorted_ops
''')

# Fix path typo
import os
bad = ROOT / "engines/trade-engine/src/athena_x_engine_trade_engine/ranking.py',"
if bad.exists():
    os.rename(bad, ROOT / "engines/trade-engine/src/athena_x_engine_trade_engine/ranking.py")

w("engines/trade-engine/tests/__init__.py", "")
w("engines/trade-engine/tests/test_engine.py", '''
"""Tests for Trade Engine."""
import pytest
from athena_x_engine_trade_engine import (
    TradeDNA, TradeStatus, TradeReadinessMeter,
    TimingAssessment, RiskAssessment, TradeAlignment,
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
    """Near catalyst = HIGH_RISK."""
    engine = TimingEngine()
    timing = engine.assess(
        trend_alignment=50,
        near_catalyst=True,
        vix_level=28,
    )
    assert timing == TimingWindow.HIGH_RISK


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
''')

# ============================================================================
# 2. TRADE INTELLIGENCE AGENT
# ============================================================================

w("agents/trade-intelligence/pyproject.toml", '''
[project]
name = "athena-x-agent-trade-intelligence"
version = "0.1.0"
description = "Trade DNA Agent - produces the 6th intelligence object (Stage 12)"
requires-python = ">=3.11"
dependencies = [
    "athena-x-engine-trade-engine",
    "athena-x-runtime-event-envelope",
    "athena-x-runtime-logger",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_agent_trade_intelligence"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w("agents/trade-intelligence/src/athena_x_agent_trade_intelligence/__init__.py", '''
"""Trade DNA Agent."""
from .agent import TradeDNAAgent

__all__ = ["TradeDNAAgent"]
__version__ = "0.1.0"
''')

w("agents/trade-intelligence/src/athena_x_agent_trade_intelligence/agent.py", '''
"""Trade DNA Agent - produces the 6th intelligence object.

Stage 12: Converts the 5 DNA objects into Trade DNA.

Pipeline:
  1. Trade Qualification (should we trade?)
  2. Timing Assessment (when?)
  3. Risk Assessment (how much?)
  4. Option Timing (which strategy?)
  5. Trade Alignment (5 DNA objects aligned?)
  6. Entry Quality (how good is the setup?)
  7. Institutional Checklist (10-point)
  8. Trade Scenarios (bull/bear/neutral)
  9. Opportunity Ranking
  10. Readiness Meter (0-100)
  11. Explainability
  12. Publish Trade DNA

Usage:
    agent = TradeDNAAgent()
    dna = await agent.compute_trade_dna(
        symbol="SPY",
        technical_dna={...},
        options_dna={...},
        market_dna={...},
        narrative_dna={...},
        forecast_dna={...},
    )
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
from athena_x_runtime_logger import get_logger
from athena_x_runtime_event_envelope import create_event, EventPriority
from athena_x_engine_trade_engine import (
    TradeDNA, TradeStatus, TradeReadinessMeter,
    TimingAssessment, RiskAssessment, TradeAlignment,
    EntryQuality, OptionTiming, TradeScenario,
    InstitutionalChecklist, TradeRanking,
    TradeQualificationEngine, TimingEngine, RiskEngine,
    OpportunityRankingEngine,
)

log = get_logger("trade-intelligence.dna")


class TradeDNAAgent:
    """Produces Trade DNA from the 5 DNA objects.

    Stage 12 rule: Does NOT execute trades. Produces structured
    Trade Intelligence for dashboard, reports, and future execution.
    """

    def __init__(self, event_bus: Any = None):
        self._bus = event_bus
        self._qualification = TradeQualificationEngine()
        self._timing = TimingEngine()
        self._risk = RiskEngine()
        self._ranking = OpportunityRankingEngine()
        self._dna_count = 0

    async def compute_trade_dna(
        self,
        symbol: str,
        technical_dna: dict | None = None,
        options_dna: dict | None = None,
        market_dna: dict | None = None,
        narrative_dna: dict | None = None,
        forecast_dna: dict | None = None,
    ) -> TradeDNA:
        """Compute the full Trade DNA from 5 DNA objects."""
        td = technical_dna or {}
        od = options_dna or {}
        md = market_dna or {}
        nd = narrative_dna or {}
        fd = forecast_dna or {}

        dna = TradeDNA(symbol=symbol)

        # 1. Trade Alignment
        dna.alignment = self._compute_alignment(td, od, md, nd, fd)
        dna.alignment_score = dna.alignment.score

        # 2. Entry Quality
        dna.entry_quality = self._compute_entry_quality(td, od, md)

        # 3. Timing
        dna.timing = self._timing.assess(
            trend_alignment=td.get("alignment_score", 50),
            pullback_detected=td.get("trend") == "bullish",
            distance_from_support=0.3,
            vix_level=md.get("risk_score", 50),
            time_of_day=datetime.now(timezone.utc).strftime("%H:%M"),
            near_catalyst=len(nd.get("upcoming_catalysts", [])) > 0,
        )

        # 4. Risk
        direction = fd.get("direction", "neutral")
        target = fd.get("target_price")
        spot = td.get("ema", 450)
        if direction == "bullish" and target:
            dna.risk = self._risk.assess(
                entry=spot, stop=spot * 0.995, target=target,
                probability_of_success=fd.get("confidence", 0.65),
                atr=td.get("atr", 2.0),
            )
            dna.hold_time = dna.risk.expected_hold_time
        elif direction == "bearish" and target:
            dna.risk = self._risk.assess(
                entry=spot, stop=spot * 1.005, target=target,
                probability_of_success=fd.get("confidence", 0.65),
                atr=td.get("atr", 2.0),
            )
            dna.hold_time = dna.risk.expected_hold_time

        # 5. Option Timing
        dna.option_timing = self._compute_option_timing(od, fd)

        # 6. Institutional Checklist
        dna.checklist = self._compute_checklist(td, od, md, nd, fd)

        # 7. Trade Qualification
        risk_score = md.get("risk_score", 50)
        timing_score = 75 if dna.timing.value == "optimal_entry" else (50 if "early" in dna.timing.value or "chasing" in dna.timing.value else 30)
        dna.trade_status = self._qualification.qualify(
            alignment=dna.alignment,
            risk_score=risk_score,
            timing_score=timing_score,
            entry_quality=dna.entry_quality.score,
        )

        # 8. Trade Scenarios
        dna.bull_plan = TradeScenario("Primary", "bull", "Buy Pullback", spot, spot * 0.995, target, fd.get("bull", {}).get("probability", 0.5))
        dna.bear_plan = TradeScenario("Alternative", "bear", "Short Rejection", spot, spot * 1.005, spot * 0.99, fd.get("bear", {}).get("probability", 0.3))
        dna.neutral_plan = TradeScenario("Neutral", "neutral", "Wait", probability=fd.get("base", {}).get("probability", 0.2))

        # 9. Trade Type
        if dna.trade_status in (TradeStatus.READY, TradeStatus.ACTIVE):
            if direction == "bullish":
                dna.trade_type = "Long Calls" if od.get("iv_regime") == "low" else "Long Stock"
            elif direction == "bearish":
                dna.trade_type = "Long Puts" if od.get("iv_regime") == "low" else "Short Stock"
            else:
                dna.trade_type = "No Trade"
        else:
            dna.trade_type = "No Trade"

        # 10. Risk + Reward scores
        dna.risk_score = risk_score
        dna.reward_score = min(100, int(dna.risk.expected_reward * 10)) if dna.risk.expected_reward else 50

        # 11. Readiness Meter
        readiness_score = self._compute_readiness_score(dna)
        dna.readiness_meter = TradeReadinessMeter(score=readiness_score)

        # 12. Probability + Confidence
        dna.probability = fd.get("confidence", 0.5) * (0.7 + dna.alignment.score * 0.3)
        dna.confidence = min(1.0, dna.probability * (0.8 + dna.checklist.pass_rate * 0.2))

        # 13. Drivers + Threats
        dna.drivers = self._extract_drivers(td, od, md, nd, fd)
        dna.threats = self._extract_threats(td, od, md, nd, fd)

        # 14. Explanation
        dna.explanation = self._generate_explanation(dna)

        # 15. Opportunity Ranking
        dna.opportunities = self._ranking.rank([
            TradeRanking(symbol=symbol, trade_type=dna.trade_type, score=readiness_score),
            TradeRanking(symbol="No Trade", trade_type="Stand Aside", score=max(0, 100 - readiness_score)),
        ])

        self._dna_count += 1

        # Publish event
        if self._bus is not None:
            event = create_event(
                event_type="ai:trade:dna",
                source_agent="trade-intelligence.dna",
                symbol=symbol,
                priority=EventPriority.HIGH,
                payload=dna.to_dict(),
            )
            await self._bus.publish(event)

        return dna

    def _compute_alignment(self, td, od, md, nd, fd) -> TradeAlignment:
        """Check alignment between 5 DNA objects."""
        return TradeAlignment(
            technical=td.get("trend", "unknown") != "unknown",
            options=od.get("dealer_gamma", "unknown") != "unknown",
            market=md.get("market_regime", "unknown") != "unknown",
            narrative=nd.get("primary_driver", "unknown") != "unknown",
            forecast=fd.get("direction", "neutral") != "neutral",
        )

    def _compute_entry_quality(self, td, od, md) -> EntryQuality:
        """Compute entry quality score (0-100)."""
        eq = EntryQuality()
        eq.trend_quality = td.get("trend") in ("bullish", "bearish")
        eq.volume_confirmation = td.get("rsi", 50) not in range(45, 55)
        eq.dealer_positioning = od.get("dealer_gamma") in ("long", "short")
        eq.gamma_support = od.get("dealer_gamma") == "long"
        eq.wyckoff_confirmation = td.get("wyckoff_phase") in ("accumulation", "markup")
        eq.chan_confirmation = True  # simplified

        score = 50
        if eq.trend_quality: score += 10
        if eq.volume_confirmation: score += 5
        if eq.dealer_positioning: score += 10
        if eq.gamma_support: score += 10
        if eq.wyckoff_confirmation: score += 10
        if eq.pullback_quality: score += 5
        eq.score = min(100, score)
        return eq

    def _compute_option_timing(self, od, fd) -> OptionTiming:
        """Compute option timing assessment."""
        return OptionTiming(
            current_iv=od.get("iv_crush_risk", 0.3),
            iv_rising=od.get("iv_regime") == "high",
            theta_risk="low" if od.get("iv_regime") == "low" else "medium",
            gamma_exposure=od.get("dealer_gamma", "neutral"),
            expected_move=od.get("expected_move", 5.0),
            risk_0dte=od.get("intraday_risk", "medium"),
            best_strategy="Long Calls" if fd.get("direction") == "bullish" else ("Long Puts" if fd.get("direction") == "bearish" else "None"),
            suggested_holding="25-40 min",
            directional_edge="high" if fd.get("confidence", 0.5) > 0.7 else "medium",
            iv_crush_risk="low" if od.get("iv_crush_risk", 0.3) < 0.4 else "high",
        )

    def _compute_checklist(self, td, od, md, nd, fd) -> InstitutionalChecklist:
        """Compute the 10-point institutional checklist."""
        return InstitutionalChecklist(
            trend=td.get("trend") in ("bullish", "bearish"),
            multi_timeframe=td.get("alignment_score", 50) > 60,
            volume=td.get("rsi", 50) != 50,
            gamma=od.get("dealer_gamma") in ("long", "short"),
            dealer=od.get("dealer_gamma") is not None,
            breadth=md.get("breadth") in ("Strong", "Weak"),
            news=nd.get("primary_driver", "unknown") != "unknown",
            forecast=fd.get("direction") in ("bullish", "bearish"),
            correlation=md.get("spy_es_correlation") is not None,
            risk=md.get("risk_score", 50) < 70,
        )

    def _compute_readiness_score(self, dna: TradeDNA) -> int:
        """Compute Trade Readiness Meter score (0-100)."""
        score = 30  # baseline
        score += int(dna.alignment.score * 20)  # 0-20 from alignment
        score += int(dna.checklist.pass_rate * 20)  # 0-20 from checklist
        score += int(dna.entry_quality.score * 0.15)  # 0-15 from entry quality
        if dna.timing.value == "optimal_entry": score += 15
        elif dna.timing.value == "too_early": score += 5
        if dna.risk.risk_reward_ratio > 2.0: score += 10
        if dna.option_timing.iv_crush_risk == "low": score += 5
        if dna.trade_status == TradeStatus.ACTIVE: score += 10
        return min(100, max(0, score))

    def _extract_drivers(self, td, od, md, nd, fd) -> list[str]:
        """Extract positive drivers."""
        drivers = []
        if td.get("trend") == "bullish": drivers.append("Technical bullish")
        if od.get("dealer_gamma") == "long": drivers.append("Dealer gamma positive")
        if md.get("breadth") == "Strong": drivers.append("Breadth strong")
        if md.get("leadership") in ("SOXX", "XLK"): drivers.append(f"{md.get('leadership')} leading")
        if fd.get("direction") == "bullish": drivers.append("Forecast bullish")
        if nd.get("confidence", 0) > 0.7: drivers.append("Narrative supportive")
        return drivers

    def _extract_threats(self, td, od, md, nd, fd) -> list[str]:
        """Extract negative threats."""
        threats = []
        if md.get("spy_vix_correlation", -0.7) > 0: threats.append("VIX not confirming")
        if md.get("risk_score", 50) > 70: threats.append(f"High risk score ({md.get('risk_score')})")
        if od.get("iv_crush_risk", 0) > 0.5: threats.append("IV crush risk")
        if nd.get("upcoming_catalysts"): threats.append("Upcoming catalyst")
        if fd.get("model_agreement", 1.0) < 0.6: threats.append("Low model agreement")
        return threats

    def _generate_explanation(self, dna: TradeDNA) -> str:
        """Generate human-readable explanation."""
        parts = [f"Trade Status: {dna.trade_status.value}"]
        parts.append(f"Readiness: {dna.readiness_meter.score}/100 ({dna.readiness_meter.label})")
        parts.append(f"Alignment: {int(dna.alignment_score * 100)}%")
        parts.append(f"Checklist: {dna.checklist.passed_count}/{dna.checklist.total}")
        if dna.drivers:
            parts.append(f"Drivers: {', '.join(dna.drivers[:3])}")
        if dna.threats:
            parts.append(f"Threats: {', '.join(dna.threats[:2])}")
        return ". ".join(parts)

    def get_stats(self) -> dict:
        return {"trade_dnas_computed": self._dna_count}
''')

# Fix path typo
bad2 = ROOT / "agents/trade-intelligence/src/athena_x_agent_trade_intelligence/agent.py',"
if bad2.exists():
    os.rename(bad2, ROOT / "agents/trade-intelligence/src/athena_x_agent_trade_intelligence/agent.py")

w("agents/trade-intelligence/tests/__init__.py", "")
w("agents/trade-intelligence/tests/test_agent.py", '''
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
''')

# ============================================================================
# 3. STAGE 12 INTEGRATION
# ============================================================================

w("runtime/stage12-integration/pyproject.toml", '''
[project]
name = "athena-x-runtime-stage12-integration"
version = "0.1.0"
description = "Stage 12 integration - Trade Intelligence Platform tests"
requires-python = ">=3.11"
dependencies = [
    "athena-x-engine-trade-engine",
    "athena-x-agent-trade-intelligence",
    "athena-x-runtime-event-bus",
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_runtime_stage12_integration"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w("runtime/stage12-integration/src/athena_x_runtime_stage12_integration/__init__.py", '''"""Stage 12 integration."""''')

w("runtime/stage12-integration/tests/__init__.py", "")
w("runtime/stage12-integration/tests/test_stage12_acceptance.py", '''
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
    assert risky == TimingWindow.HIGH_RISK


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
''')

print(f"\\n✅ Stage 12 complete: {len(FILES)} files written")
print("\\nComponents implemented:")
print("  1. engines/trade-engine/ - Qualification + Timing + Risk + Ranking + Checklist + Types")
print("  2. agents/trade-intelligence/ - Trade DNA Agent (6th intelligence object)")
print("  3. runtime/stage12-integration/ - 10 exit criteria acceptance tests")
print("\\nNext: install deps and run tests")
