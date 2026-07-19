"""Tests for Forecast DNA Agent + Market Memory Service."""
import pytest
from athena_x_agent_forecast_intelligence import ForecastDNAAgent, MarketMemoryService
from athena_x_plugin_forecast_base import (
    ForecastOutput, ForecastInput, ForecastHorizon, ModelHealth,
)


class FakeModel:
    """Fake forecast model for testing."""
    def __init__(self, model_id, direction, target, confidence=0.8):
        self._id = model_id
        self._direction = direction
        self._target = target
        self._confidence = confidence

    @property
    def model_id(self): return self._id
    @property
    def version(self): return "1.0.0"
    @property
    def runtime(self): return "cpu"

    def forecast(self, input_data):
        return ForecastOutput(
            model_id=self._id,
            direction=self._direction,
            target_price=self._target,
            confidence=self._confidence,
            horizon=input_data.horizon,
        )

    def get_health(self):
        return ModelHealth(model_id=self._id)


# ============================================================================
# Forecast DNA Agent tests
# ============================================================================

@pytest.fixture
def agent():
    a = ForecastDNAAgent()
    a.set_models([
        FakeModel("lstm", "bullish", 458, 0.85),
        FakeModel("xgboost", "bullish", 457, 0.75),
        FakeModel("arima", "neutral", 455, 0.6),
    ])
    return a


async def test_forecast_dna_produced(agent):
    """Forecast DNA Agent produces a ForecastDNA object."""
    dna = await agent.compute_forecast(
        symbol="SPY",
        technical_dna={"trend": "bullish", "rsi": 45},
        options_dna={"dealer_gamma": "long"},
        market_dna={"market_regime": "Risk-On"},
        narrative_dna={"primary_driver": "Fed dovish", "confidence": 0.85},
    )
    assert dna.symbol == "SPY"
    assert dna.direction in ("bullish", "bearish", "neutral")
    assert dna.confidence_matrix is not None


async def test_forecast_dna_includes_scenarios(agent):
    """Forecast DNA includes Bull/Base/Bear scenarios."""
    dna = await agent.compute_forecast(symbol="SPY")
    assert dna.bull.scenario.value == "bull"
    assert dna.base.scenario.value == "base"
    assert dna.bear.scenario.value == "bear"
    # Probabilities sum to ~1.0
    total = dna.bull.probability + dna.base.probability + dna.bear.probability
    assert 0.95 < total < 1.05


async def test_forecast_dna_includes_confidence_matrix(agent):
    """Forecast DNA includes a 7-source confidence matrix."""
    dna = await agent.compute_forecast(
        symbol="SPY",
        technical_dna={"trend": "bullish"},
        options_dna={"dealer_gamma": "long"},
        market_dna={"market_regime": "Risk-On"},
        narrative_dna={"confidence": 0.85},
    )
    cm = dna.confidence_matrix
    assert cm.technical_confidence > 0
    assert cm.options_confidence > 0
    assert cm.market_confidence > 0
    assert cm.narrative_confidence > 0
    assert cm.model_agreement > 0
    assert cm.data_freshness > 0
    assert cm.final_confidence > 0


async def test_forecast_dna_includes_explanation(agent):
    """Forecast DNA includes human-readable explanation."""
    dna = await agent.compute_forecast(
        symbol="SPY",
        technical_dna={"trend": "bullish"},
        options_dna={"dealer_gamma": "long"},
        market_dna={"market_regime": "Risk-On", "breadth": "Strong"},
    )
    assert len(dna.explanation.positive_factors) > 0
    assert len(dna.explanation.summary) > 0


async def test_forecast_dna_includes_model_agreement(agent):
    """Forecast DNA includes model agreement score."""
    dna = await agent.compute_forecast(symbol="SPY")
    assert 0 <= dna.model_agreement <= 1.0
    assert len(dna.models_consulted) == 3


async def test_forecast_dna_event_published(agent):
    """Forecast DNA publishes ai:forecast:dna event."""
    from athena_x_runtime_event_bus import InMemoryBusClient

    bus = InMemoryBusClient()
    agent._bus = bus

    received = []
    async def handler(event):
        received.append(event)
    await bus.subscribe("ai:forecast:dna", handler)

    await agent.compute_forecast(symbol="SPY")

    assert len(received) == 1
    assert "direction" in received[0].payload
    await bus.close()


async def test_forecast_dna_includes_drivers_and_threats(agent):
    """Forecast DNA includes drivers and threats."""
    dna = await agent.compute_forecast(
        symbol="SPY",
        technical_dna={"trend": "bullish"},
        market_dna={"market_regime": "Risk-On"},
    )
    assert isinstance(dna.drivers, list)
    assert isinstance(dna.threats, list)


# ============================================================================
# Market Memory Service tests
# ============================================================================

def test_market_memory_records_and_retrieves():
    """Market Memory records conditions and finds similar entries."""
    memory = MarketMemoryService()
    memory.record(
        fingerprint={"trend": "bullish", "regime": "Risk-On", "dealer_gamma": "long"},
        outcome={"direction": "bullish", "return_15min": 0.002},
    )
    memory.record(
        fingerprint={"trend": "bearish", "regime": "Risk-Off"},
        outcome={"direction": "bearish", "return_15min": -0.003},
    )

    matches = memory.find_similar({"trend": "bullish", "regime": "Risk-On"})
    assert len(matches) > 0
    assert matches[0].actual_outcome["direction"] == "bullish"


def test_market_memory_ranks_by_similarity():
    """Market Memory ranks results by similarity score."""
    memory = MarketMemoryService()
    memory.record({"trend": "bullish", "regime": "Risk-On"}, {"direction": "bullish"})
    memory.record({"trend": "bullish", "regime": "Risk-Off"}, {"direction": "neutral"})
    memory.record({"trend": "bearish", "regime": "Risk-Off"}, {"direction": "bearish"})

    # Query for bullish + Risk-On
    matches = memory.find_similar({"trend": "bullish", "regime": "Risk-On"})
    # Best match should be the first entry
    assert matches[0].dna_fingerprint["regime"] == "Risk-On"
    assert matches[0].dna_fingerprint["trend"] == "bullish"


def test_market_memory_stats():
    memory = MarketMemoryService()
    memory.record({"trend": "bullish"}, {"direction": "bullish"})
    stats = memory.get_stats()
    assert stats["total_entries"] == 1
