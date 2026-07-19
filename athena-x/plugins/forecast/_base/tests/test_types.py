"""Tests for Forecast types."""
import pytest
from athena_x_plugin_forecast_base import (
    ForecastPlugin, ForecastInput, ForecastOutput,
    ForecastDNA, ScenarioDNA, ConfidenceMatrix,
    ModelHealth, ForecastHorizon, Scenario,
    ExplainabilityResult,
)


def test_7_forecast_horizons():
    assert ForecastHorizon.NEXT_5MIN.value == "5min"
    assert ForecastHorizon.NEXT_15MIN.value == "15min"
    assert ForecastHorizon.NEXT_30MIN.value == "30min"
    assert ForecastHorizon.NEXT_1HOUR.value == "1hour"
    assert ForecastHorizon.END_OF_SESSION.value == "EOS"
    assert ForecastHorizon.OVERNIGHT.value == "overnight"
    assert ForecastHorizon.TOMORROW.value == "tomorrow"


def test_3_scenarios():
    assert Scenario.BULL.value == "bull"
    assert Scenario.BASE.value == "base"
    assert Scenario.BEAR.value == "bear"


def test_forecast_dna_has_all_fields():
    dna = ForecastDNA(symbol="SPY", direction="bullish", target_price=458.0)
    assert dna.direction == "bullish"
    assert dna.target_price == 458.0
    assert dna.bull.scenario == Scenario.BULL
    assert dna.confidence_matrix is not None
    assert dna.explanation is not None


def test_forecast_dna_serializable():
    dna = ForecastDNA(symbol="ES", direction="bearish")
    d = dna.to_dict()
    assert d["symbol"] == "ES"
    assert d["direction"] == "bearish"
    assert "confidence_breakdown" in d


def test_confidence_matrix_7_sources():
    cm = ConfidenceMatrix(
        technical_confidence=0.9,
        options_confidence=0.85,
        market_confidence=0.8,
        narrative_confidence=0.75,
        model_agreement=0.88,
        data_freshness=0.95,
        final_confidence=0.87,
    )
    assert cm.technical_confidence == 0.9
    assert cm.final_confidence == 0.87


def test_scenario_dna():
    s = ScenarioDNA(
        scenario=Scenario.BULL,
        probability=0.58,
        target_price=458.0,
        expected_path="Pullback -> Breakout -> Trend",
    )
    assert s.probability == 0.58
    assert "Breakout" in s.expected_path


def test_model_health():
    h = ModelHealth(model_id="lstm", directional_accuracy=0.65, weight=0.8)
    assert h.model_id == "lstm"
    assert h.directional_accuracy == 0.65


def test_explainability():
    e = ExplainabilityResult(
        positive_factors=["Technical DNA bullish", "Dealer gamma positive"],
        negative_factors=["DXY strengthening"],
        summary="Bullish bias with some headwinds from FX",
    )
    assert len(e.positive_factors) == 2
    assert len(e.negative_factors) == 1


def test_protocol_is_runtime_checkable():
    class FakeModel:
        @property
        def model_id(self): return "test"
        @property
        def version(self): return "1.0.0"
        @property
        def runtime(self): return "python-gpu"
        def forecast(self, inp): return ForecastOutput(model_id="test")
        def get_health(self): return ModelHealth(model_id="test")

    model = FakeModel()
    assert isinstance(model, ForecastPlugin)
