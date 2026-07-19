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
