"""Forecast DNA Agent - produces the 5th intelligence object.

Stage 11: Fuses the 4 DNA objects (Technical, Options, Market, Narrative)
into a single ForecastDNA for downstream decision-making.

Pipeline:
  1. Feature Fusion (4 DNA objects -> canonical feature vector)
  2. Run all model plugins
  3. Ensemble Consensus (regime-aware weighting)
  4. Generate Bull/Base/Bear scenarios
  5. Build Confidence Matrix
  6. Generate Explainability
  7. Publish ForecastDNA as ai:forecast:* event
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
from athena_x_runtime_logger import get_logger
from athena_x_runtime_event_envelope import create_event, EventPriority
from athena_x_engine_forecast_engine import (
    FeatureFusion, EnsembleConsensus,
    ForecastValidator, ExplainabilityEngine,
)
from athena_x_plugin_forecast_base import (
    ForecastDNA, ScenarioDNA, ConfidenceMatrix,
    ForecastOutput, ForecastHorizon, Scenario,
    ModelHealth, ForecastInput,
)

log = get_logger("forecast-intelligence.dna")


class ForecastDNAAgent:
    """Produces ForecastDNA from the 4 DNA objects + model plugins.

    Usage:
        agent = ForecastDNAAgent()
        agent.set_models([lstm_model, xgboost_model, rule_model])
        dna = await agent.compute_forecast(
            symbol="SPY",
            technical_dna={...},
            options_dna={...},
            market_dna={...},
            narrative_dna={...},
        )
    """

    def __init__(self, event_bus: Any = None):
        self._bus = event_bus
        self._fusion = FeatureFusion()
        self._ensemble = EnsembleConsensus()
        self._validator = ForecastValidator()
        self._explainability = ExplainabilityEngine()
        self._models: list[Any] = []  # ForecastPlugin instances
        self._dna_count = 0

    def set_models(self, models: list[Any]) -> None:
        """Set the forecast model plugins to use."""
        self._models = models

    async def compute_forecast(
        self,
        symbol: str,
        technical_dna: dict | None = None,
        options_dna: dict | None = None,
        market_dna: dict | None = None,
        narrative_dna: dict | None = None,
        horizon: ForecastHorizon = ForecastHorizon.NEXT_15MIN,
    ) -> ForecastDNA:
        """Compute the full Forecast DNA."""
        # 1. Feature Fusion
        forecast_input = self._fusion.fuse(
            technical_dna=technical_dna,
            options_dna=options_dna,
            market_dna=market_dna,
            narrative_dna=narrative_dna,
            symbol=symbol,
            horizon=horizon,
        )

        # 2. Run all models
        outputs: list[ForecastOutput] = []
        for model in self._models:
            try:
                output = model.forecast(forecast_input)
                outputs.append(output)
                # Record for validation
                self._validator.record_forecast(output.model_id, output.target_price, output.direction)
            except Exception as e:
                log.warning("model_failed", model_id=getattr(model, "model_id", "unknown"), error=str(e))

        # 3. Get model healths
        model_healths = {}
        for output in outputs:
            health = self._validator.get_health(output.model_id)
            model_healths[output.model_id] = health

        # 4. Ensemble Consensus
        market_regime = (market_dna or {}).get("market_regime", "unknown")
        vol_regime = (market_dna or {}).get("volatility", "unknown")
        consensus, agreement = self._ensemble.combine(
            outputs=outputs,
            model_healths=model_healths,
            market_regime=market_regime,
            volatility_regime=vol_regime,
        )

        # 5. Generate scenarios
        bull, base, bear = self._generate_scenarios(consensus, forecast_input)

        # 6. Confidence Matrix
        confidence_matrix = self._build_confidence_matrix(
            technical_dna or {},
            options_dna or {},
            market_dna or {},
            narrative_dna or {},
            agreement,
        )

        # 7. Explainability
        explanation = self._explainability.explain(
            direction=consensus.direction,
            features=forecast_input.features,
            model_outputs=outputs,
        )

        # 8. Build Forecast DNA
        dna = ForecastDNA(
            timestamp=datetime.now(timezone.utc),
            symbol=symbol,
            horizon=horizon,
            direction=consensus.direction,
            target_price=consensus.target_price,
            expected_path=self._generate_path(consensus.direction, bull, base, bear),
            bull=bull,
            base=base,
            bear=bear,
            confidence_matrix=confidence_matrix,
            model_agreement=agreement,
            models_consulted=[o.model_id for o in outputs],
            risk_level=consensus.risk_estimate,
            drivers=explanation.positive_factors,
            threats=explanation.negative_factors,
            explanation=explanation,
            model_health_summary={
                mid: {
                    "directional_accuracy": h.directional_accuracy,
                    "weight": h.weight,
                    "prediction_count": h.prediction_count,
                }
                for mid, h in model_healths.items()
            },
        )

        self._dna_count += 1

        # Publish event
        if self._bus is not None:
            event = create_event(
                event_type=f"ai:forecast:dna",
                source_agent="forecast-intelligence.dna",
                symbol=symbol,
                priority=EventPriority.HIGH,
                payload=dna.to_dict(),
            )
            await self._bus.publish(event)

        return dna

    def _generate_scenarios(
        self,
        consensus: ForecastOutput,
        forecast_input: ForecastInput,
    ) -> tuple[ScenarioDNA, ScenarioDNA, ScenarioDNA]:
        """Generate Bull/Base/Bear scenarios."""
        target = consensus.target_price or 0
        confidence = consensus.confidence

        if consensus.direction == "bullish":
            bull_prob = 0.40 + confidence * 0.20
            base_prob = 0.30
            bear_prob = 1.0 - bull_prob - base_prob
        elif consensus.direction == "bearish":
            bear_prob = 0.40 + confidence * 0.20
            base_prob = 0.30
            bull_prob = 1.0 - bear_prob - base_prob
        else:
            bull_prob = base_prob = bear_prob = 0.33

        bull = ScenarioDNA(
            scenario=Scenario.BULL,
            probability=round(bull_prob, 4),
            target_price=round(target * 1.01, 4) if target else None,
            expected_path="Pullback -> Breakout -> Trend",
            key_drivers=["Positive momentum", "Supportive gamma"],
        )
        base = ScenarioDNA(
            scenario=Scenario.BASE,
            probability=round(base_prob, 4),
            target_price=round(target, 4) if target else None,
            expected_path="Range-bound -> Slight drift",
            key_drivers=["Neutral positioning"],
        )
        bear = ScenarioDNA(
            scenario=Scenario.BEAR,
            probability=round(bear_prob, 4),
            target_price=round(target * 0.99, 4) if target else None,
            expected_path="Failed breakout -> Reversal -> Down",
            key_drivers=["Negative divergence", "VIX not confirming"],
        )

        return bull, base, bear

    def _build_confidence_matrix(
        self,
        technical: dict,
        options: dict,
        market: dict,
        narrative: dict,
        model_agreement: float,
    ) -> ConfidenceMatrix:
        """Build the confidence matrix from all sources."""
        tech_conf = 0.5 + (0.3 if technical.get("trend") != "unknown" else 0)
        opt_conf = 0.5 + (0.3 if options.get("dealer_gamma") != "unknown" else 0)
        mkt_conf = 0.5 + (0.2 if market.get("market_regime") != "unknown" else 0)
        nar_conf = narrative.get("confidence", 0.5)

        # Data freshness (simplified)
        freshness = 0.9  # would be computed from timestamps

        final = (tech_conf + opt_conf + mkt_conf + nar_conf + model_agreement + freshness) / 6

        return ConfidenceMatrix(
            technical_confidence=round(tech_conf, 4),
            options_confidence=round(opt_conf, 4),
            market_confidence=round(mkt_conf, 4),
            narrative_confidence=round(nar_conf, 4),
            model_agreement=round(model_agreement, 4),
            data_freshness=round(freshness, 4),
            final_confidence=round(final, 4),
        )

    def _generate_path(self, direction: str, bull: ScenarioDNA, base: ScenarioDNA, bear: ScenarioDNA) -> str:
        """Generate expected path description."""
        if direction == "bullish":
            return "Pullback -> Breakout -> Trend continuation"
        elif direction == "bearish":
            return "Relief rally -> Failed breakout -> Reversal"
        return "Range-bound with slight drift"

    def get_stats(self) -> dict:
        return {
            "forecasts_computed": self._dna_count,
            "models_loaded": len(self._models),
        }
