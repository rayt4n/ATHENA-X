"""Ensemble Consensus Engine - regime-aware model weighting.

Stage 11 req: Weight models based on:
  - Historical performance
  - Current market regime
  - Volatility regime
  - Trend/range conditions
  - Economic calendar
  - Time of day

Example:
  Trending market -> trend-following models get higher weight
  High-volatility event day -> volatility-aware models dominate
  Range day -> mean-reversion models gain weight
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from athena_x_plugin_forecast_base import (
    ForecastOutput, ForecastDNA, ScenarioDNA, ConfidenceMatrix,
    ModelHealth, Scenario, ForecastHorizon,
)
from athena_x_runtime_logger import get_logger

log = get_logger("forecast.ensemble")


class EnsembleConsensus:
    """Combines individual model forecasts into a single consensus.

    Usage:
        ensemble = EnsembleConsensus()
        consensus = ensemble.combine(
            outputs=[lstm_output, xgboost_output, rule_output],
            model_healths={"lstm": health_lstm, ...},
            market_regime="Risk-On",
            volatility_regime="Normal",
        )
    """

    def combine(
        self,
        outputs: list[ForecastOutput],
        model_healths: dict[str, ModelHealth] | None = None,
        market_regime: str = "unknown",
        volatility_regime: str = "unknown",
    ) -> tuple[ForecastOutput, float]:
        """Combine multiple model outputs into a consensus.

        Returns (consensus_output, model_agreement_score).
        """
        if not outputs:
            return ForecastOutput(model_id="ensemble"), 0.0

        model_healths = model_healths or {}

        # Calculate regime-aware weights
        weights = self._compute_weights(outputs, model_healths, market_regime, volatility_regime)

        # Weighted vote on direction
        direction_scores = {"bullish": 0.0, "bearish": 0.0, "neutral": 0.0}
        weighted_target = 0.0
        total_weight = 0.0
        weighted_confidence = 0.0

        for output in outputs:
            w = weights.get(output.model_id, 1.0)
            direction_scores[output.direction] = direction_scores.get(output.direction, 0) + w
            if output.target_price is not None:
                weighted_target += output.target_price * w
            weighted_confidence += output.confidence * w
            total_weight += w

        # Determine consensus direction
        consensus_direction = max(direction_scores, key=direction_scores.get)

        # Model agreement: how much models agree
        max_direction_weight = max(direction_scores.values())
        model_agreement = max_direction_weight / total_weight if total_weight > 0 else 0.0

        # Weighted target
        consensus_target = weighted_target / total_weight if total_weight > 0 and weighted_target > 0 else None
        consensus_confidence = weighted_confidence / total_weight if total_weight > 0 else 0.5

        consensus = ForecastOutput(
            model_id="ensemble",
            direction=consensus_direction,
            target_price=consensus_target,
            confidence=consensus_confidence,
            horizon=outputs[0].horizon if outputs else ForecastHorizon.NEXT_15MIN,
            risk_estimate=self._assess_risk(consensus_confidence, model_agreement, volatility_regime),
            metadata={
                "models_consulted": [o.model_id for o in outputs],
                "weights": weights,
                "direction_scores": direction_scores,
            },
        )

        return consensus, model_agreement

    def _compute_weights(
        self,
        outputs: list[ForecastOutput],
        healths: dict[str, ModelHealth],
        market_regime: str,
        volatility_regime: str,
    ) -> dict[str, float]:
        """Compute regime-aware weights for each model."""
        weights = {}
        for output in outputs:
            health = healths.get(output.model_id)
            base_weight = health.weight if health else 1.0

            # Adjust based on regime
            if market_regime == "Risk-On" and output.model_id in ("lstm", "transformer", "rule_based"):
                base_weight *= 1.2  # trend-following models
            elif market_regime == "Risk-Off" and output.model_id in ("xgboost", "lightgbm"):
                base_weight *= 1.1  # tree-based models
            elif "Range" in market_regime or market_regime == "Neutral":
                if output.model_id in ("arima", "random_forest"):
                    base_weight *= 1.15  # mean-reversion

            # Adjust for volatility
            if volatility_regime == "Expanding":
                if output.model_id in ("lstm", "transformer"):
                    base_weight *= 1.1  # deep learning handles vol better

            weights[output.model_id] = base_weight

        # Normalize
        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}

        return weights

    def _assess_risk(self, confidence: float, agreement: float, vol_regime: str) -> str:
        """Assess overall risk level."""
        if vol_regime == "Expanding" or agreement < 0.6:
            return "high"
        elif confidence > 0.8 and agreement > 0.8:
            return "low"
        return "medium"
