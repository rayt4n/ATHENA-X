"""ForecastModel Protocol - the stable interface for all AI forecast models.

Stage 5.1: Plugin architecture - stable interface from day one.

Routing rule (non-overridable):
  - LSTM, Transformer, TabPFN, XGBoost, CatBoost, LightGBM-large -> Python GPU
  - LightGBM-small, RandomForest, LogisticRegression -> Browser ONNX
  - LSTM NEVER runs in browser.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol, runtime_checkable


class ModelRuntime(str, Enum):
    """Where the model runs."""
    PYTHON_GPU = "python-gpu"
    BROWSER_ONNX = "browser-onnx"


@dataclass
class ModelConfig:
    """Configuration for a forecast model."""
    model_id: str  # "lstm", "transformer", "xgboost", etc.
    runtime: ModelRuntime
    version: str = "1.0.0"
    horizon: str = "1D"  # 1D, 1W, 1M, 3M, 6M
    weights: dict[str, float] = field(default_factory=dict)  # feature weights
    hyperparams: dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelInput:
    """Input data for a forecast model."""
    symbol: str
    features: dict[str, list[float]]  # e.g., {"returns": [...], "volume": [...]}
    target: list[float] | None = None  # for training
    timestamps: list[int] = field(default_factory=list)


@dataclass
class ModelOutput:
    """Output of a forecast model."""
    model_id: str
    symbol: str
    runtime: ModelRuntime
    predictions: list[float]  # predicted prices or probabilities
    confidence: list[float] = field(default_factory=list)
    inference_time_ms: float = 0.0
    model_version: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class ForecastModel(Protocol):
    """Stable interface for all AI forecast models.

    Every model implements this protocol. New models can be added
    without changing any consumer code.

    Usage:
        model: ForecastModel = LSTMModel(config)
        result = model.predict(input_data)
    """

    @property
    def model_id(self) -> str:
        """Model ID (e.g., 'lstm', 'transformer', 'xgboost')."""
        ...

    @property
    def runtime(self) -> ModelRuntime:
        """Where the model runs (PYTHON_GPU or BROWSER_ONNX)."""
        ...

    @property
    def version(self) -> str:
        """Model version (semver)."""
        ...

    def predict(self, input_data: ModelInput) -> ModelOutput:
        """Generate a forecast.

        Args:
            input_data: features for the symbol

        Returns:
            ModelOutput with predictions + confidence.
        """
        ...

    def train(self, training_data: ModelInput) -> None:
        """Train the model (optional - some models are pre-trained)."""
        ...

    def validate_input(self, input_data: ModelInput) -> list[str]:
        """Validate input. Returns list of error messages (empty if valid)."""
        ...
