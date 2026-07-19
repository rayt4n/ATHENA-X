"""Confidence Arbitration Engine - resolves disagreements among 6 DNA objects.

Stage 13 req: Do not average intelligence objects. Identify conflicts,
explain why they exist, weight sources by regime, publish consensus.
"""
from __future__ import annotations
from typing import Any
from athena_x_engine_governance_engine.types import ConfidenceArbitration
from athena_x_runtime_logger import get_logger

log = get_logger("governance.confidence_arbitration")


class ConfidenceArbitrationEngine:
    """Resolves disagreements among the 6 intelligence objects.

    Usage:
        engine = ConfidenceArbitrationEngine()
        result = engine.arbitrate(
            technical="bullish",
            options="bearish",
            market="neutral",
            narrative="bullish",
            forecast="bearish",
            trade="watch",
            market_regime="Risk-On",
        )
        # result.consensus_direction = "neutral"
        # result.conflicts = ["Technical vs Options disagreement", ...]
    """

    def arbitrate(
        self,
        technical: str = "neutral",
        options: str = "neutral",
        market: str = "neutral",
        narrative: str = "neutral",
        forecast: str = "neutral",
        trade: str = "neutral",
        market_regime: str = "unknown",
    ) -> ConfidenceArbitration:
        """Arbitrate among the 6 intelligence objects."""
        directions = {
            "technical": technical,
            "options": options,
            "market": market,
            "narrative": narrative,
            "forecast": forecast,
            "trade": trade,
        }

        # Identify conflicts
        conflicts = []
        bullish_sources = [k for k, v in directions.items() if v == "bullish"]
        bearish_sources = [k for k, v in directions.items() if v == "bearish"]

        if bullish_sources and bearish_sources:
            conflicts.append(
                f"Bullish ({', '.join(bullish_sources)}) vs Bearish ({', '.join(bearish_sources)})"
            )

        # Weight by regime
        weights = self._get_regime_weights(market_regime)

        # Weighted vote
        weighted_bullish = sum(weights.get(k, 1.0) for k in bullish_sources)
        weighted_bearish = sum(weights.get(k, 1.0) for k in bearish_sources)

        if weighted_bullish > weighted_bearish * 1.3:
            consensus = "bullish"
        elif weighted_bearish > weighted_bullish * 1.3:
            consensus = "bearish"
        else:
            consensus = "neutral"

        # Trust score: higher when objects agree
        total_sources = len([v for v in directions.values() if v != "neutral"])
        if total_sources == 0:
            trust = 0.5
        else:
            agreement = max(weighted_bullish, weighted_bearish) / (weighted_bullish + weighted_bearish) if (weighted_bullish + weighted_bearish) > 0 else 1.0
            trust = agreement * 0.8 + 0.2  # baseline trust

        explanation = self._generate_explanation(directions, consensus, conflicts, trust)

        return ConfidenceArbitration(
            technical_direction=technical,
            options_direction=options,
            market_direction=market,
            narrative_direction=narrative,
            forecast_direction=forecast,
            trade_direction=trade,
            conflicts=conflicts,
            consensus_direction=consensus,
            trust_score=round(trust, 4),
            explanation=explanation,
        )

    def _get_regime_weights(self, regime: str) -> dict[str, float]:
        """Get source weights based on market regime."""
        if regime == "Risk-On":
            return {"technical": 1.2, "forecast": 1.2, "options": 1.0, "market": 1.0, "narrative": 0.8, "trade": 1.0}
        elif regime == "Risk-Off":
            return {"options": 1.3, "market": 1.2, "narrative": 1.1, "technical": 0.9, "forecast": 0.9, "trade": 1.0}
        else:
            return {"technical": 1.0, "options": 1.0, "market": 1.0, "narrative": 1.0, "forecast": 1.0, "trade": 1.0}

    def _generate_explanation(self, directions: dict, consensus: str, conflicts: list[str], trust: float) -> str:
        parts = [f"Consensus: {consensus}"]
        if conflicts:
            parts.append(f"Conflicts: {len(conflicts)}")
            parts.extend(conflicts[:2])
        parts.append(f"Trust score: {trust:.2f}")
        return ". ".join(parts)
