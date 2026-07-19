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
