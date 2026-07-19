"""Tests for ForecastModel Protocol."""
import pytest
from athena_x_forecast_model_base import (
    ForecastModel, ModelInput, ModelOutput, ModelConfig, ModelRuntime,
)


class FakeXGBoostModel:
    """Test implementation of ForecastModel."""
    @property
    def model_id(self) -> str:
        return "xgboost"
    @property
    def runtime(self) -> ModelRuntime:
        return ModelRuntime.PYTHON_GPU
    @property
    def version(self) -> str:
        return "1.0.0"
    def predict(self, input_data):
        features = input_data.features.get("returns", [])
        if not features:
            return ModelOutput(model_id="xgboost", symbol=input_data.symbol, runtime=ModelRuntime.PYTHON_GPU, predictions=[])
        # Simple: predict last value + small drift
        last = features[-1]
        predictions = [last * 1.01, last * 1.02, last * 1.03]
        return ModelOutput(
            model_id="xgboost", symbol=input_data.symbol, runtime=ModelRuntime.PYTHON_GPU,
            predictions=predictions, confidence=[0.8, 0.7, 0.6],
        )
    def train(self, training_data):
        pass  # pre-trained in this fake
    def validate_input(self, input_data):
        errors = []
        if not input_data.features:
            errors.append("features must not be empty")
        return errors


def test_protocol_is_runtime_checkable():
    model = FakeXGBoostModel()
    assert isinstance(model, ForecastModel)


def test_model_has_id():
    model = FakeXGBoostModel()
    assert model.model_id == "xgboost"


def test_model_has_runtime():
    model = FakeXGBoostModel()
    assert model.runtime == ModelRuntime.PYTHON_GPU


def test_predict_returns_output():
    model = FakeXGBoostModel()
    input_data = ModelInput(
        symbol="SPY",
        features={"returns": [0.01, 0.02, -0.01, 0.03]},
    )
    result = model.predict(input_data)
    assert isinstance(result, ModelOutput)
    assert result.model_id == "xgboost"
    assert len(result.predictions) == 3


def test_validate_input_returns_errors():
    model = FakeXGBoostModel()
    bad_input = ModelInput(symbol="SPY", features={})
    errors = model.validate_input(bad_input)
    assert len(errors) > 0


def test_model_runtime_enum():
    assert ModelRuntime.PYTHON_GPU.value == "python-gpu"
    assert ModelRuntime.BROWSER_ONNX.value == "browser-onnx"


def test_model_config_has_required_fields():
    config = ModelConfig(
        model_id="lstm",
        runtime=ModelRuntime.PYTHON_GPU,
    )
    assert config.model_id == "lstm"
    assert config.runtime == ModelRuntime.PYTHON_GPU
    assert config.horizon == "1D"
