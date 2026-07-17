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
