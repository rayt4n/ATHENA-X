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
    TimingWindow, RiskAssessment, TradeAlignment,
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
