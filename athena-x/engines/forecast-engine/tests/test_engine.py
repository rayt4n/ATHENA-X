"""Tests for Forecast Engine."""
import pytest
from athena_x_plugin_forecast_base import (
    ForecastInput, ForecastOutput, ForecastHorizon,
    ModelHealth, Scenario,
)
from athena_x_engine_forecast_engine import (
    FeatureFusion, EnsembleConsensus,
    ForecastValidator, ExplainabilityEngine,
)


# ============================================================================
# Feature Fusion tests
# ============================================================================

def test_fusion_produces_feature_vector():
    """Feature Fusion creates a canonical feature vector from 4 DNA objects."""
    fusion = FeatureFusion()
    inp = fusion.fuse(
        technical_dna={"trend": "bullish", "rsi": 45, "ema": 450, "alignment_score": 82},
        options_dna={"dealer_gamma": "long", "iv_regime": "low", "expected_move": 5.2},
        market_dna={"market_regime": "Risk-On", "breadth": "Strong", "risk_score": 25},
        narrative_dna={"primary_driver": "CPI lower", "confidence": 0.85},
        symbol="SPY",
    )
    assert inp.symbol == "SPY"
    assert inp.features["trend"] == "bullish"
    assert inp.features["dealer_gamma"] == "long"
    assert inp.features["market_regime"] == "Risk-On"
    assert inp.features["primary_driver"] == "CPI lower"


def test_fusion_includes_all_4_dna_sources():
    """Feature vector includes features from all 4 DNA objects."""
    fusion = FeatureFusion()
    inp = fusion.fuse(
        technical_dna={"trend": "bullish"},
        options_dna={"dealer_gamma": "long"},
        market_dna={"market_regime": "Risk-On"},
        narrative_dna={"current_theme": "Growth"},
    )
    features = inp.features
    # Technical
    assert "trend" in features
    assert "rsi" in features
    # Options
    assert "dealer_gamma" in features
    assert "iv_regime" in features
    # Market
    assert "market_regime" in features
    assert "breadth" in features
    # Narrative
    assert "current_theme" in features
    assert "narrative_confidence" in features


def test_fusion_includes_session_context():
    """Feature vector includes session context (hour, minute, day)."""
    fusion = FeatureFusion()
    inp = fusion.fuse()
    assert "hour" in inp.features
    assert "minute" in inp.features
    assert "day_of_week" in inp.features


# ============================================================================
# Ensemble Consensus tests
# ============================================================================

def test_ensemble_combines_outputs():
    """Ensemble produces a consensus from multiple model outputs."""
    ensemble = EnsembleConsensus()
    outputs = [
        ForecastOutput(model_id="lstm", direction="bullish", target_price=458, confidence=0.8),
        ForecastOutput(model_id="xgboost", direction="bullish", target_price=457, confidence=0.75),
        ForecastOutput(model_id="arima", direction="neutral", target_price=455, confidence=0.6),
    ]
    consensus, agreement = ensemble.combine(outputs)
    assert consensus.direction == "bullish"
    assert agreement > 0.5  # 2 of 3 agree


def test_ensemble_weights_by_regime():
    """Ensemble adjusts weights based on market regime."""
    ensemble = EnsembleConsensus()
    outputs = [
        ForecastOutput(model_id="lstm", direction="bullish", confidence=0.8),
        ForecastOutput(model_id="arima", direction="bearish", confidence=0.6),
    ]
    # Trending market -> LSTM gets higher weight
    consensus, agreement = ensemble.combine(outputs, market_regime="Risk-On")
    assert consensus.direction == "bullish"  # LSTM dominates


def test_ensemble_agreement_score():
    """Model agreement score reflects how much models agree."""
    ensemble = EnsembleConsensus()
    # All agree
    outputs_agree = [
        ForecastOutput(model_id="a", direction="bullish"),
        ForecastOutput(model_id="b", direction="bullish"),
        ForecastOutput(model_id="c", direction="bullish"),
    ]
    _, agreement_high = ensemble.combine(outputs_agree)
    assert agreement_high > 0.9

    # Disagree
    outputs_disagree = [
        ForecastOutput(model_id="a", direction="bullish"),
        ForecastOutput(model_id="b", direction="bearish"),
    ]
    _, agreement_low = ensemble.combine(outputs_disagree)
    assert agreement_low < agreement_high


def test_ensemble_assesses_risk():
    """Ensemble assesses risk based on confidence + agreement + volatility."""
    ensemble = EnsembleConsensus()
    outputs = [ForecastOutput(model_id="a", direction="bullish", confidence=0.5)]
    consensus, _ = ensemble.combine(outputs, volatility_regime="Expanding")
    assert consensus.risk_estimate == "high"


# ============================================================================
# Forecast Validator tests
# ============================================================================

def test_validator_records_forecast_and_actual():
    """Validator tracks forecast accuracy."""
    validator = ForecastValidator()
    validator.record_forecast("lstm", target=458.0, direction="bullish")
    validator.record_actual("lstm", actual_price=456.0, actual_direction="bullish")

    health = validator.get_health("lstm")
    assert health.model_id == "lstm"
    assert health.directional_accuracy == 1.0  # direction correct
    assert health.rolling_mae is not None


def test_validator_downweights_poor_models():
    """Poor-performing models get lower weight."""
    validator = ForecastValidator()
    # Record several wrong forecasts
    for _ in range(5):
        validator.record_forecast("bad_model", target=460, direction="bullish")
        validator.record_actual("bad_model", actual_price=450, actual_direction="bearish")

    health = validator.get_health("bad_model")
    assert health.weight < 1.0  # downweighted
    assert health.directional_accuracy < 0.5


def test_validator_upweights_good_models():
    """Good-performing models get higher weight."""
    validator = ForecastValidator()
    for _ in range(5):
        validator.record_forecast("good_model", target=458, direction="bullish")
        validator.record_actual("good_model", actual_price=458, actual_direction="bullish")

    health = validator.get_health("good_model")
    assert health.weight > 1.0  # upweighted
    assert health.directional_accuracy == 1.0


# ============================================================================
# Explainability tests
# ============================================================================

def test_explainability_produces_factors():
    """Explainability engine produces positive + negative factors."""
    engine = ExplainabilityEngine()
    explanation = engine.explain(
        direction="bullish",
        features={
            "trend": "bullish",
            "rsi": 28,
            "dealer_gamma": "long",
            "breadth": "Strong",
            "market_regime": "Risk-On",
            "alignment_score": 82,
        },
    )
    assert len(explanation.positive_factors) > 0
    assert "Technical DNA bullish" in explanation.positive_factors


def test_explainability_includes_summary():
    """Explanation includes a human-readable summary."""
    engine = ExplainabilityEngine()
    explanation = engine.explain("bullish", {"trend": "bullish", "breadth": "Strong"})
    assert len(explanation.summary) > 0


def test_explainability_detects_threats():
    """Explanation detects negative factors / threats."""
    engine = ExplainabilityEngine()
    explanation = engine.explain(
        direction="bullish",
        features={
            "spy_vix_correlation": 0.3,  # VIX not confirming
            "risk_score": 75,  # high risk
        },
    )
    assert len(explanation.negative_factors) > 0
