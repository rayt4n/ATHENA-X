"""Explainability Engine - produces human-readable forecast explanations.

Stage 11 req: Every forecast should answer "Why?"

Example:
  Bullish because:
  + Technical DNA bullish
  + Dealer gamma positive
  + Breadth improving
  + SOXX leading
  + Narrative supportive

  Negative factors:
  - DXY strengthening
  - Treasury yields rising
"""
from __future__ import annotations
from typing import Any
from athena_x_plugin_forecast_base import ExplainabilityResult, ForecastOutput
from athena_x_runtime_logger import get_logger

log = get_logger("forecast.explainability")


class ExplainabilityEngine:
    """Generates human-readable explanations for forecasts.

    Usage:
        engine = ExplainabilityEngine()
        explanation = engine.explain(
            direction="bullish",
            features={...},  # the fused feature vector
            model_outputs=[...],
        )
    """

    def explain(
        self,
        direction: str,
        features: dict[str, Any],
        model_outputs: list[ForecastOutput] | None = None,
    ) -> ExplainabilityResult:
        """Generate an explanation for a forecast direction."""
        positive = []
        negative = []

        # Technical factors
        trend = features.get("trend", "unknown")
        if trend == "bullish" and direction == "bullish":
            positive.append("Technical DNA bullish")
        elif trend == "bearish" and direction == "bearish":
            positive.append("Technical DNA bearish (confirming)")
        elif trend == "bullish" and direction == "bearish":
            negative.append("Technical DNA bullish (diverging)")

        rsi = features.get("rsi", 50)
        if rsi < 30 and direction == "bullish":
            positive.append("RSI oversold (< 30)")
        elif rsi > 70 and direction == "bearish":
            positive.append("RSI overbought (> 70)")

        alignment = features.get("alignment_score", 50)
        if alignment > 70 and direction == "bullish":
            positive.append(f"Multi-timeframe alignment {alignment}%")
        elif alignment < 30 and direction == "bearish":
            positive.append(f"Multi-timeframe misalignment ({alignment}%)")

        # Options factors
        dealer_gamma = features.get("dealer_gamma", "unknown")
        if dealer_gamma == "long" and direction == "bullish":
            positive.append("Dealer gamma positive")
        elif dealer_gamma == "short" and direction == "bearish":
            positive.append("Dealer gamma negative")

        iv_regime = features.get("iv_regime", "unknown")
        if iv_regime == "low" and direction == "bullish":
            positive.append("IV regime low (favorable for longs)")
        elif iv_regime == "high" and direction == "bearish":
            positive.append("IV regime high (unfavorable)")

        # Market factors
        breadth = features.get("breadth", "unknown")
        if breadth == "Strong" and direction == "bullish":
            positive.append("Breadth improving")
        elif breadth == "Weak" and direction == "bearish":
            positive.append("Breadth weakening")

        leadership = features.get("leadership", "unknown")
        if leadership in ("XLK", "SOXX", "XLY") and direction == "bullish":
            positive.append(f"{leadership} leading")

        regime = features.get("market_regime", "unknown")
        if regime == "Risk-On" and direction == "bullish":
            positive.append("Market regime Risk-On")
        elif regime == "Risk-Off" and direction == "bearish":
            positive.append("Market regime Risk-Off")

        # Narrative factors
        theme = features.get("current_theme", "unknown")
        narrative_conf = features.get("narrative_confidence", 0.5)
        if narrative_conf > 0.7:
            positive.append(f"Narrative supportive ({theme}, {narrative_conf:.0%})")

        # Threats
        spy_vix_corr = features.get("spy_vix_correlation", -0.7)
        if spy_vix_corr > 0 and direction == "bullish":
            negative.append("VIX not confirming")

        risk_score = features.get("risk_score", 50)
        if risk_score > 70:
            negative.append(f"High risk score ({risk_score}/100)")

        # Summary
        summary_parts = []
        if positive:
            summary_parts.append(f"Bullish bias from {len(positive)} positive factors")
        if negative:
            summary_parts.append(f"{len(negative)} negative factors")
        summary = ". ".join(summary_parts) if summary_parts else "Neutral outlook"

        return ExplainabilityResult(
            positive_factors=positive,
            negative_factors=negative,
            summary=summary,
        )
