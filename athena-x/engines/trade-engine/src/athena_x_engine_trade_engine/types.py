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
