#!/usr/bin/env python3
"""
STEP 4 Stage 11 - Forecast & Scenario Platform
================================================
Implements:
  1. plugins/forecast/_base/ - ForecastPlugin Protocol + ForecastDNA types
  2. 9 forecast model plugin manifests (ARIMA, LSTM, BiLSTM, Transformer, XGBoost, LightGBM, RF, TabPFN, RuleBased)
  3. engines/forecast-engine/ - Feature Fusion + Ensemble + Validation + Explainability
  4. agents/forecast-intelligence/ - Forecast DNA Agent + Market Memory Service
  5. runtime/stage11-integration/ - acceptance tests

Key: Fuses 4 DNA objects into Forecast DNA (5th intelligence object).

Run: python /home/z/my-project/scripts/stage11_implement.py
"""

from pathlib import Path
import textwrap

ROOT = Path("/home/z/my-project/athena-x")
ROOT.mkdir(parents=True, exist_ok=True)
FILES = []

def w(rel: str, content: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(content).lstrip("\n"))
    FILES.append(rel)


# ============================================================================
# 1. FORECAST PLUGIN PROTOCOL + FORECAST DNA TYPES
# ============================================================================

w("plugins/forecast/_base/pyproject.toml", '''
[project]
name = "athena-x-plugin-forecast-base"
version = "0.1.0"
description = "ForecastPlugin Protocol + ForecastDNA + ScenarioDNA types (Stage 11)"
requires-python = ">=3.11"
dependencies = ["pydantic>=2.9.0"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_plugin_forecast_base"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w("plugins/forecast/_base/src/athena_x_plugin_forecast_base/__init__.py", '''
"""ForecastPlugin Protocol + ForecastDNA types."""
from .types import (
    ForecastPlugin, ForecastInput, ForecastOutput,
    ForecastDNA, ScenarioDNA, ConfidenceMatrix,
    ModelHealth, ForecastHorizon, Scenario,
    ExplainabilityResult,
)

__all__ = [
    "ForecastPlugin", "ForecastInput", "ForecastOutput",
    "ForecastDNA", "ScenarioDNA", "ConfidenceMatrix",
    "ModelHealth", "ForecastHorizon", "Scenario",
    "ExplainabilityResult",
]
__version__ = "0.1.0"
''')

w("plugins/forecast/_base/src/athena_x_plugin_forecast_base/types.py", '''
"""Forecast types - Stage 11.

The 5th intelligence object: Forecast DNA.

Fuses the 4 DNA objects (Technical, Options, Market, Narrative) into
multiple independent forecasts, compares them, and produces a single
institutional forecast for downstream decision-making.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Protocol, runtime_checkable


class ForecastHorizon(str, Enum):
    """Multi-horizon forecasts aligned with intraday trading."""
    NEXT_5MIN = "5min"
    NEXT_15MIN = "15min"       # primary intraday horizon
    NEXT_30MIN = "30min"
    NEXT_1HOUR = "1hour"
    END_OF_SESSION = "EOS"
    OVERNIGHT = "overnight"
    TOMORROW = "tomorrow"


class Scenario(str, Enum):
    BULL = "bull"
    BASE = "base"
    BEAR = "bear"


@dataclass
class ForecastInput:
    """Input to a forecast model - the canonical feature vector.

    Built by Feature Fusion from the 4 DNA objects.
    """
    symbol: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    # Features from the 4 DNA objects
    features: dict[str, Any] = field(default_factory=dict)
    # Which horizon to forecast
    horizon: ForecastHorizon = ForecastHorizon.NEXT_15MIN


@dataclass
class ForecastOutput:
    """Output from a single forecast model."""
    model_id: str
    direction: str = "neutral"        # bullish, bearish, neutral
    target_price: float | None = None
    confidence: float = 0.5
    horizon: ForecastHorizon = ForecastHorizon.NEXT_15MIN
    risk_estimate: str = "medium"     # low, medium, high
    feature_importance: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ScenarioDNA:
    """Bull/Base/Bear scenario with probability + target + path."""
    scenario: Scenario
    probability: float = 0.33
    target_price: float | None = None
    expected_path: str = ""           # "Pullback -> Breakout -> Trend"
    key_drivers: list[str] = field(default_factory=list)


@dataclass
class ConfidenceMatrix:
    """Confidence broken down by source (not a single opaque number)."""
    technical_confidence: float = 0.5
    options_confidence: float = 0.5
    market_confidence: float = 0.5
    narrative_confidence: float = 0.5
    model_agreement: float = 0.5
    data_freshness: float = 0.5
    final_confidence: float = 0.5


@dataclass
class ModelHealth:
    """Health metrics for a forecast model."""
    model_id: str
    last_prediction_error: float | None = None
    rolling_mae: float | None = None
    rolling_rmse: float | None = None
    directional_accuracy: float = 0.5
    regime_accuracy: float = 0.5
    calibration_score: float = 0.5
    weight: float = 1.0  # current ensemble weight
    prediction_count: int = 0


@dataclass
class ExplainabilityResult:
    """Human-readable explanation of a forecast."""
    positive_factors: list[str] = field(default_factory=list)
    negative_factors: list[str] = field(default_factory=list)
    summary: str = ""


@dataclass
class ForecastDNA:
    """The 5th intelligence object - Forecast DNA.

    Consumed by Stage 12 (Probability), Stage 13 (Supervisor),
    Stage 15 (Reports).
    """
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    symbol: str = ""
    horizon: ForecastHorizon = ForecastHorizon.NEXT_15MIN

    # Primary forecast
    direction: str = "neutral"
    target_price: float | None = None
    expected_path: str = ""

    # Scenarios
    bull: ScenarioDNA = field(default_factory=lambda: ScenarioDNA(Scenario.BULL))
    base: ScenarioDNA = field(default_factory=lambda: ScenarioDNA(Scenario.BASE))
    bear: ScenarioDNA = field(default_factory=lambda: ScenarioDNA(Scenario.BEAR))

    # Confidence
    confidence_matrix: ConfidenceMatrix = field(default_factory=ConfidenceMatrix)

    # Model agreement
    model_agreement: float = 0.5  # 0..1, how much models agree
    models_consulted: list[str] = field(default_factory=list)

    # Risk
    risk_level: str = "medium"

    # Explainability
    drivers: list[str] = field(default_factory=list)
    threats: list[str] = field(default_factory=list)
    explanation: ExplainabilityResult = field(default_factory=ExplainabilityResult)

    # Model health summary
    model_health_summary: dict[str, dict] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "symbol": self.symbol,
            "horizon": self.horizon.value,
            "direction": self.direction,
            "target_price": self.target_price,
            "expected_path": self.expected_path,
            "bull_probability": self.bull.probability,
            "base_probability": self.base.probability,
            "bear_probability": self.bear.probability,
            "bull_target": self.bull.target_price,
            "base_target": self.base.target_price,
            "bear_target": self.bear.target_price,
            "confidence": self.confidence_matrix.final_confidence,
            "model_agreement": self.model_agreement,
            "risk_level": self.risk_level,
            "drivers": self.drivers,
            "threats": self.threats,
            "explanation": {
                "positive_factors": self.explanation.positive_factors,
                "negative_factors": self.explanation.negative_factors,
                "summary": self.explanation.summary,
            },
            "models_consulted": self.models_consulted,
            "confidence_breakdown": {
                "technical": self.confidence_matrix.technical_confidence,
                "options": self.confidence_matrix.options_confidence,
                "market": self.confidence_matrix.market_confidence,
                "narrative": self.confidence_matrix.narrative_confidence,
                "model_agreement": self.confidence_matrix.model_agreement,
                "data_freshness": self.confidence_matrix.data_freshness,
            },
        }


@runtime_checkable
class ForecastPlugin(Protocol):
    """Stable interface for all forecast model plugins.

    Each model is independent. No model knows about the others.
    Adding a new model = adding a folder.
    """

    @property
    def model_id(self) -> str: ...

    @property
    def version(self) -> str: ...

    @property
    def runtime(self) -> str: ...  # "python-gpu" or "browser-onnx"

    def forecast(self, input_data: ForecastInput) -> ForecastOutput: ...

    def get_health(self) -> ModelHealth: ...
''')

w("plugins/forecast/_base/tests/__init__.py", "")
w("plugins/forecast/_base/tests/test_types.py", '''
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
''')

# ============================================================================
# 2. FORECAST MODEL MANIFESTS (9 models)
# ============================================================================

FORECAST_MODELS = [
    ("arima", "ARIMA", "statistical", "cpu", 1, "Statistical ARIMA model"),
    ("lstm", "LSTM", "deep_learning", "python-gpu", 5, "PyTorch LSTM (NEVER browser)"),
    ("bilstm_attention", "BiLSTM Attention", "deep_learning", "python-gpu", 5, "BiLSTM with attention (NEVER browser)"),
    ("transformer", "Transformer", "deep_learning", "python-gpu", 5, "Transformer (NEVER browser)"),
    ("xgboost", "XGBoost", "gradient_boosting", "python-gpu", 3, "XGBoost classifier"),
    ("lightgbm", "LightGBM", "gradient_boosting", "python-gpu", 3, "LightGBM classifier"),
    ("random_forest", "Random Forest", "ensemble", "browser-onnx", 3, "Random Forest (browser ONNX)"),
    ("tabpfn", "TabPFN", "in_context", "python-gpu", 10, "TabPFN in-context learning"),
    ("rule_based", "Rule-Based", "rules", "cpu", 1, "Rule-based forecast from DNA objects"),
]

for slug, name, category, runtime, refresh, desc in FORECAST_MODELS:
    w(f"plugins/forecast/{slug}/manifest.yaml", f'''id: {slug}
name: "{name}"
version: "1.0.0"
category: {category}
runtime: {runtime}
refresh_interval_seconds: {refresh}
inputs: [features]
outputs: [direction, target_price, confidence, risk_estimate]
dependencies: []
enabled: true
description: "{desc}"
author: "ATHENA-X"
''')

# ============================================================================
# 3. FORECAST ENGINE
# ============================================================================

w("engines/forecast-engine/pyproject.toml", '''
[project]
name = "athena-x-engine-forecast-engine"
version = "0.1.0"
description = "Forecast Engine - Feature Fusion + Ensemble + Validation + Explainability"
requires-python = ">=3.11"
dependencies = [
    "athena-x-plugin-forecast-base",
    "athena-x-runtime-logger",
    "athena-x-runtime-event-envelope",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_engine_forecast_engine"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w("engines/forecast-engine/src/athena_x_engine_forecast_engine/__init__.py", '''
"""Forecast Engine."""
from .fusion import FeatureFusion
from .ensemble import EnsembleConsensus
from .validation import ForecastValidator
from .explainability import ExplainabilityEngine

__all__ = [
    "FeatureFusion", "EnsembleConsensus",
    "ForecastValidator", "ExplainabilityEngine",
]
__version__ = "0.1.0"
''')

w("engines/forecast-engine/src/athena_x_engine_forecast_engine/fusion.py", '''
"""Feature Fusion Layer - converts 4 DNA objects into canonical feature vector.

Stage 11 req: Before any model runs, all four DNA objects are converted
into a single canonical feature vector. This ensures every model receives
identical inputs.
"""
from __future__ import annotations
from typing import Any
from athena_x_plugin_forecast_base import ForecastInput, ForecastHorizon


class FeatureFusion:
    """Fuses Technical DNA, Options DNA, Market DNA, Narrative DNA.

    Usage:
        fusion = FeatureFusion()
        features = fusion.fuse(
            technical_dna={...},
            options_dna={...},
            market_dna={...},
            narrative_dna={...},
            symbol="SPY",
        )
        # features is a flat dict that any model can consume
    """

    def fuse(
        self,
        technical_dna: dict | None = None,
        options_dna: dict | None = None,
        market_dna: dict | None = None,
        narrative_dna: dict | None = None,
        symbol: str = "SPY",
        horizon: ForecastHorizon = ForecastHorizon.NEXT_15MIN,
    ) -> ForecastInput:
        """Fuse the 4 DNA objects into a canonical feature vector."""
        features: dict[str, Any] = {}

        # Technical DNA features
        td = technical_dna or {}
        features["trend"] = td.get("trend", "unknown")
        features["rsi"] = td.get("rsi", 50)
        features["ema"] = td.get("ema", 0)
        features["macd_histogram"] = td.get("macd", {}).get("histogram", 0) if isinstance(td.get("macd"), dict) else 0
        features["atr"] = td.get("atr", 0)
        features["adx"] = td.get("adx", 25)
        features["alignment_score"] = td.get("alignment_score", 50)
        features["bollinger_percent_b"] = td.get("bollinger", {}).get("percent_b", 0.5) if isinstance(td.get("bollinger"), dict) else 0.5

        # Options DNA features
        od = options_dna or {}
        features["dealer_gamma"] = od.get("dealer_gamma", "unknown")
        features["gamma_flip"] = od.get("gamma_flip_level", 0)
        features["iv_regime"] = od.get("iv_regime", "unknown")
        features["iv_crush_risk"] = od.get("iv_crush_risk", 0)
        features["expected_move"] = od.get("expected_move", 0)
        features["positioning"] = od.get("positioning", "unknown")
        features["intraday_risk"] = od.get("intraday_risk", "unknown")

        # Market DNA features
        md = market_dna or {}
        features["market_regime"] = md.get("market_regime", "unknown")
        features["volatility"] = md.get("volatility", "unknown")
        features["liquidity"] = md.get("liquidity", "unknown")
        features["breadth"] = md.get("breadth", "unknown")
        features["leadership"] = md.get("leadership", "unknown")
        features["risk_score"] = md.get("risk_score", 50)
        features["spy_es_correlation"] = md.get("spy_es_correlation", 0.95) or 0.95
        features["spy_vix_correlation"] = md.get("spy_vix_correlation", -0.7) or -0.7

        # Narrative DNA features
        nd = narrative_dna or {}
        features["primary_driver"] = nd.get("primary_driver", "unknown")
        features["current_theme"] = nd.get("current_theme", "unknown")
        features["narrative_confidence"] = nd.get("confidence", 0.5)
        features["active_event_count"] = len(nd.get("active_events", []))
        features["catalyst_count"] = len(nd.get("upcoming_catalysts", []))

        # Session context
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        features["hour"] = now.hour
        features["minute"] = now.minute
        features["day_of_week"] = now.weekday()

        return ForecastInput(
            symbol=symbol,
            timestamp=now,
            features=features,
            horizon=horizon,
        )
''')

w("engines/forecast-engine/src/athena_x_engine_forecast_engine/ensemble.py", '''
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
''')

w("engines/forecast-engine/src/athena_x_engine_forecast_engine/validation.py", '''
"""Forecast Validator - continuous self-validation.

Stage 11 req: Do not wait until tomorrow. Continuously compare:
  Forecast -> Actual -> Error -> Update Model Health
"""
from __future__ import annotations
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import RLock
from typing import Any
from athena_x_plugin_forecast_base import ModelHealth
from athena_x_runtime_logger import get_logger

log = get_logger("forecast.validation")


class ForecastValidator:
    """Continuously validates forecast accuracy against live market data.

    Usage:
        validator = ForecastValidator()
        validator.record_forecast("lstm", target=458.0, direction="bullish")
        # ... later, when actual price is known ...
        validator.record_actual("lstm", actual=456.0)
        health = validator.get_health("lstm")
    """

    def __init__(self, window: int = 100):
        self._forecasts: dict[str, list[dict]] = {}  # model_id -> [{target, direction, timestamp}]
        self._errors: dict[str, deque] = {}           # model_id -> deque of errors
        self._directional_hits: dict[str, int] = {}
        self._directional_total: dict[str, int] = {}
        self._window = window
        self._lock = RLock()

    def record_forecast(self, model_id: str, target: float | None, direction: str) -> None:
        """Record a forecast made by a model."""
        with self._lock:
            self._forecasts.setdefault(model_id, []).append({
                "target": target,
                "direction": direction,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            # Keep only recent forecasts
            if len(self._forecasts[model_id]) > self._window:
                self._forecasts[model_id] = self._forecasts[model_id][-self._window:]

    def record_actual(self, model_id: str, actual_price: float, actual_direction: str) -> None:
        """Record the actual outcome for a model's forecast."""
        with self._lock:
            forecasts = self._forecasts.get(model_id, [])
            if not forecasts:
                return

            # Match with oldest unvalidated forecast
            forecast = forecasts.pop(0)
            target = forecast.get("target")
            predicted_direction = forecast.get("direction", "neutral")

            # Compute error
            if target is not None:
                error = abs(actual_price - target)
                self._errors.setdefault(model_id, deque(maxlen=self._window)).append(error)

            # Track directional accuracy
            self._directional_total[model_id] = self._directional_total.get(model_id, 0) + 1
            if predicted_direction == actual_direction:
                self._directional_hits[model_id] = self._directional_hits.get(model_id, 0) + 1

    def get_health(self, model_id: str) -> ModelHealth:
        """Get current health metrics for a model."""
        with self._lock:
            errors = list(self._errors.get(model_id, []))
            total = self._directional_total.get(model_id, 0)
            hits = self._directional_hits.get(model_id, 0)

            mae = sum(errors) / len(errors) if errors else None
            rmse = (sum(e ** 2 for e in errors) / len(errors)) ** 0.5 if errors else None
            dir_acc = hits / total if total > 0 else 0.5

            # Adjust weight based on performance
            weight = 1.0
            if dir_acc > 0.65:
                weight = 1.2
            elif dir_acc < 0.40:
                weight = 0.6

            return ModelHealth(
                model_id=model_id,
                rolling_mae=mae,
                rolling_rmse=rmse,
                directional_accuracy=dir_acc,
                weight=weight,
                prediction_count=total,
            )

    def get_all_health(self) -> dict[str, ModelHealth]:
        """Get health for all tracked models."""
        with self._lock:
            return {mid: self.get_health(mid) for mid in self._forecasts.keys()}
''')

w("engines/forecast-engine/src/athena_x_engine_forecast_engine/explainability.py", '''
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
''')

w("engines/forecast-engine/tests/__init__.py", "")
w("engines/forecast-engine/tests/test_engine.py", '''
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
''')

# ============================================================================
# 4. FORECAST INTELLIGENCE AGENT + MARKET MEMORY
# ============================================================================

w("agents/forecast-intelligence/pyproject.toml", '''
[project]
name = "athena-x-agent-forecast-intelligence"
version = "0.1.0"
description = "Forecast DNA Agent + Market Memory Service (Stage 11)"
requires-python = ">=3.11"
dependencies = [
    "athena-x-engine-forecast-engine",
    "athena-x-runtime-event-envelope",
    "athena-x-runtime-logger",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_agent_forecast_intelligence"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w("agents/forecast-intelligence/src/athena_x_agent_forecast_intelligence/__init__.py", '''
"""Forecast DNA Agent + Market Memory Service."""
from .forecast_agent import ForecastDNAAgent
from .market_memory import MarketMemoryService

__all__ = ["ForecastDNAAgent", "MarketMemoryService"]
__version__ = "0.1.0"
''')

w("agents/forecast-intelligence/src/athena_x_agent_forecast_intelligence/forecast_agent.py", '''
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
''')

w("agents/forecast-intelligence/src/athena_x_agent_forecast_intelligence/market_memory.py", '''
"""Market Memory Service - records how similar market conditions behaved historically.

Stage 11 additional req: Before models forecast, they can query:
  "Have we seen this combination of Technical DNA + Options DNA + Market DNA + Narrative DNA before?"
  "What happened next in those cases?"

This historical context strengthens forecasts without coupling to any specific model.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import RLock
from typing import Any
from athena_x_runtime_logger import get_logger

log = get_logger("forecast.market_memory")


@dataclass
class MarketMemoryEntry:
    """A historical market memory entry."""
    timestamp: datetime
    dna_fingerprint: dict[str, Any]  # key features from the 4 DNA objects
    actual_outcome: dict[str, Any]   # what actually happened
    # e.g., {"direction": "bullish", "return_15min": 0.002, "return_1hour": 0.005}


class MarketMemoryService:
    """Records and retrieves historical market condition matches.

    Usage:
        memory = MarketMemoryService()
        memory.record(fingerprint={"trend": "bullish", "regime": "Risk-On"}, outcome={"direction": "bullish"})
        matches = memory.find_similar({"trend": "bullish", "regime": "Risk-On"})
        # matches is a list of historical outcomes for similar conditions
    """

    def __init__(self, max_entries: int = 10000):
        self._entries: list[MarketMemoryEntry] = []
        self._lock = RLock()
        self._max = max_entries

    def record(self, fingerprint: dict[str, Any], outcome: dict[str, Any]) -> None:
        """Record a market condition + its outcome."""
        with self._lock:
            self._entries.append(MarketMemoryEntry(
                timestamp=datetime.now(timezone.utc),
                dna_fingerprint=dict(fingerprint),
                actual_outcome=dict(outcome),
            ))
            if len(self._entries) > self._max:
                self._entries = self._entries[-self._max:]

    def find_similar(self, fingerprint: dict[str, Any], limit: int = 10) -> list[MarketMemoryEntry]:
        """Find historical entries with similar fingerprints."""
        with self._lock:
            scored = []
            for entry in self._entries:
                score = self._similarity_score(fingerprint, entry.dna_fingerprint)
                scored.append((score, entry))
            scored.sort(key=lambda x: x[0], reverse=True)
            return [entry for _, entry in scored[:limit]]

    def _similarity_score(self, a: dict, b: dict) -> float:
        """Compute similarity score between two fingerprints (0..1)."""
        if not a or not b:
            return 0.0
        matches = 0
        total = 0
        for key in a:
            if key in b:
                total += 1
                if a[key] == b[key]:
                    matches += 1
                elif isinstance(a[key], (int, float)) and isinstance(b[key], (int, float)):
                    # Numeric similarity
                    diff = abs(a[key] - b[key])
                    matches += max(0, 1 - diff)
        return matches / total if total > 0 else 0.0

    def get_stats(self) -> dict:
        with self._lock:
            return {"total_entries": len(self._entries)}
''')

w("agents/forecast-intelligence/tests/__init__.py", "")
w("agents/forecast-intelligence/tests/test_agents.py", '''
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
''')

# ============================================================================
# 5. STAGE 11 INTEGRATION
# ============================================================================

w("runtime/stage11-integration/pyproject.toml", '''
[project]
name = "athena-x-runtime-stage11-integration"
version = "0.1.0"
description = "Stage 11 integration - Forecast & Scenario Platform tests"
requires-python = ">=3.11"
dependencies = [
    "athena-x-engine-forecast-engine",
    "athena-x-agent-forecast-intelligence",
    "athena-x-runtime-event-bus",
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_runtime_stage11_integration"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w("runtime/stage11-integration/src/athena_x_runtime_stage11_integration/__init__.py", '''"""Stage 11 integration."""''')

w("runtime/stage11-integration/tests/__init__.py", "")
w("runtime/stage11-integration/tests/test_stage11_acceptance.py", '''
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
''')

print(f"\\n✅ Stage 11 complete: {len(FILES)} files written")
print("\\nComponents implemented:")
print("  1. plugins/forecast/_base/ - ForecastPlugin Protocol + ForecastDNA types")
print("  2. plugins/forecast/*/manifest.yaml - 9 model plugin manifests")
print("  3. engines/forecast-engine/ - Feature Fusion + Ensemble + Validator + Explainability")
print("  4. agents/forecast-intelligence/ - Forecast DNA Agent + Market Memory Service")
print("  5. runtime/stage11-integration/ - 10 exit criteria acceptance tests")
print("\\nNext: install deps and run tests")
