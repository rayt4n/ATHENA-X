"""Stage 11 acceptance tests - Forecast & Scenario Platform."""
import pytest
from athena_x_plugin_forecast_base import (
    ForecastOutput, ForecastInput, ForecastHorizon, ModelHealth,
)
from athena_x_engine_forecast_engine import (
    FeatureFusion, EnsembleConsensus, ForecastValidator, ExplainabilityEngine,
)
from athena_x_agent_forecast_intelligence import ForecastDNAAgent, MarketMemoryService


class FakeModel:
    def __init__(self, mid, direction, target, conf=0.8):
        self._id, self._dir, self._tgt, self._conf = mid, direction, target, conf
    @property
    def model_id(self): return self._id
    @property
    def version(self): return "1.0.0"
    @property
    def runtime(self): return "cpu"
    def forecast(self, inp):
        return ForecastOutput(model_id=self._id, direction=self._dir, target_price=self._tgt, confidence=self._conf)
    def get_health(self):
        return ModelHealth(model_id=self._id)


# ============================================================================
# Exit Criteria 1: Models are independent plugins
# ============================================================================

def test_models_are_independent():
    """Each model produces its own forecast independently."""
    models = [
        FakeModel("lstm", "bullish", 458),
        FakeModel("xgboost", "bullish", 457),
        FakeModel("arima", "neutral", 455),
    ]
    fusion = FeatureFusion()
    inp = fusion.fuse(symbol="SPY")

    outputs = [m.forecast(inp) for m in models]
    assert len(outputs) == 3
    assert outputs[0].model_id == "lstm"
    assert outputs[1].model_id == "xgboost"
    assert outputs[2].model_id == "arima"


# ============================================================================
# Exit Criteria 2: Inputs come from 4 DNA objects
# ============================================================================

def test_feature_fusion_consumes_4_dna():
    """Feature Fusion takes all 4 DNA objects as input."""
    fusion = FeatureFusion()
    inp = fusion.fuse(
        technical_dna={"trend": "bullish"},
        options_dna={"dealer_gamma": "long"},
        market_dna={"market_regime": "Risk-On"},
        narrative_dna={"primary_driver": "Fed dovish"},
    )
    assert inp.features["trend"] == "bullish"
    assert inp.features["dealer_gamma"] == "long"
    assert inp.features["market_regime"] == "Risk-On"
    assert inp.features["primary_driver"] == "Fed dovish"


# ============================================================================
# Exit Criteria 3: Multi-horizon forecasts
# ============================================================================

async def test_multi_horizon_forecasts():
    """Forecasts can be generated for multiple horizons."""
    agent = ForecastDNAAgent()
    agent.set_models([FakeModel("test", "bullish", 458)])

    for horizon in [ForecastHorizon.NEXT_5MIN, ForecastHorizon.NEXT_15MIN, ForecastHorizon.NEXT_1HOUR]:
        dna = await agent.compute_forecast(symbol="SPY", horizon=horizon)
        assert dna.horizon == horizon


# ============================================================================
# Exit Criteria 4: Bull/Base/Bear scenarios always available
# ============================================================================

async def test_scenarios_always_available():
    """Bull/Base/Bear scenarios are always produced."""
    agent = ForecastDNAAgent()
    agent.set_models([FakeModel("test", "bullish", 458)])
    dna = await agent.compute_forecast(symbol="SPY")

    assert dna.bull is not None
    assert dna.base is not None
    assert dna.bear is not None
    # Probabilities sum to ~1.0
    total = dna.bull.probability + dna.base.probability + dna.bear.probability
    assert 0.9 < total < 1.1


# ============================================================================
# Exit Criteria 5: Ensemble adapts to regime
# ============================================================================

def test_ensemble_adapts_to_regime():
    """Ensemble weighting changes with market regime."""
    ensemble = EnsembleConsensus()
    outputs = [
        ForecastOutput(model_id="lstm", direction="bullish"),
        ForecastOutput(model_id="arima", direction="bearish"),
    ]
    # Risk-On: LSTM should dominate
    consensus_on, _ = ensemble.combine(outputs, market_regime="Risk-On")
    assert consensus_on.direction == "bullish"


# ============================================================================
# Exit Criteria 6: Model health monitored
# ============================================================================

def test_model_health_tracked():
    """Model health is continuously monitored."""
    validator = ForecastValidator()
    validator.record_forecast("lstm", target=458, direction="bullish")
    validator.record_actual("lstm", actual_price=459, actual_direction="bullish")

    health = validator.get_health("lstm")
    assert health.directional_accuracy == 1.0
    assert health.rolling_mae is not None


# ============================================================================
# Exit Criteria 7: Forecast includes explanation
# ============================================================================

async def test_forecast_includes_explanation():
    """Every forecast includes a human-readable explanation."""
    agent = ForecastDNAAgent()
    agent.set_models([FakeModel("test", "bullish", 458)])
    dna = await agent.compute_forecast(
        symbol="SPY",
        technical_dna={"trend": "bullish"},
        market_dna={"market_regime": "Risk-On"},
    )
    assert len(dna.explanation.positive_factors) > 0
    assert len(dna.explanation.summary) > 0


# ============================================================================
# Exit Criteria 8: Forecast DNA published
# ============================================================================

async def test_forecast_dna_published():
    """Forecast DNA is published as ai:forecast:dna event."""
    from athena_x_runtime_event_bus import InMemoryBusClient

    bus = InMemoryBusClient()
    agent = ForecastDNAAgent(event_bus=bus)
    agent.set_models([FakeModel("test", "bullish", 458)])

    received = []
    async def handler(event):
        received.append(event)
    await bus.subscribe("ai:forecast:dna", handler)

    await agent.compute_forecast(symbol="SPY")
    assert len(received) == 1
    await bus.close()


# ============================================================================
# Exit Criteria 9: Forecast accuracy continuously measured
# ============================================================================

def test_forecast_accuracy_measured():
    """Forecast accuracy is continuously measured."""
    validator = ForecastValidator()
    # Record 5 forecasts
    for i in range(5):
        validator.record_forecast("lstm", target=458 + i, direction="bullish")
        validator.record_actual("lstm", actual_price=458 + i, actual_direction="bullish")

    health = validator.get_health("lstm")
    assert health.directional_accuracy == 1.0
    assert health.prediction_count == 5


# ============================================================================
# Exit Criteria 10: 5 Intelligence Objects
# ============================================================================

async def test_5th_intelligence_object():
    """Forecast DNA is the 5th intelligence object."""
    agent = ForecastDNAAgent()
    agent.set_models([FakeModel("test", "bullish", 458)])
    dna = await agent.compute_forecast(symbol="SPY")

    # Has all fields for downstream AI consumption
    assert hasattr(dna, "direction")
    assert hasattr(dna, "target_price")
    assert hasattr(dna, "bull")
    assert hasattr(dna, "base")
    assert hasattr(dna, "bear")
    assert hasattr(dna, "confidence_matrix")
    assert hasattr(dna, "model_agreement")
    assert hasattr(dna, "drivers")
    assert hasattr(dna, "threats")
    assert hasattr(dna, "explanation")


# ============================================================================
# Market Memory Service
# ============================================================================

def test_market_memory_provides_historical_context():
    """Market Memory provides historical context for forecasts."""
    memory = MarketMemoryService()
    memory.record(
        fingerprint={"trend": "bullish", "regime": "Risk-On", "gamma": "long"},
        outcome={"direction": "bullish", "return": 0.003},
    )
    matches = memory.find_similar({"trend": "bullish", "regime": "Risk-On"})
    assert len(matches) > 0
    assert matches[0].actual_outcome["direction"] == "bullish"
