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
