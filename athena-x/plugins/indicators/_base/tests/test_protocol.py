"""Tests for TechnicalIndicator Protocol."""
import pytest
from athena_x_plugin_indicator_base import (
    TechnicalIndicator, IndicatorInput, IndicatorOutput, IndicatorParams,
)


class FakeEMAIndicator:
    """Test implementation of TechnicalIndicator."""
    @property
    def name(self) -> str:
        return "EMA"
    @property
    def version(self) -> str:
        return "1.0.0"
    @property
    def required_inputs(self) -> list[str]:
        return ["closes"]
    def compute(self, input_data, params=None):
        params = params or IndicatorParams(period=20)
        closes = input_data.closes
        # Simple EMA calculation
        if not closes:
            return IndicatorOutput(indicator_name="EMA", symbol=input_data.symbol, timeframe=input_data.timeframe, values={})
        multiplier = 2 / (params.period + 1)
        ema = [closes[0]]
        for i in range(1, len(closes)):
            ema.append(closes[i] * multiplier + ema[-1] * (1 - multiplier))
        return IndicatorOutput(
            indicator_name="EMA", symbol=input_data.symbol, timeframe=input_data.timeframe,
            values={"ema": ema},
        )
    def validate_params(self, params):
        errors = []
        if params.period < 1:
            errors.append("period must be >= 1")
        return errors


def test_protocol_is_runtime_checkable():
    """TechnicalIndicator is a runtime-checkable Protocol."""
    indicator = FakeEMAIndicator()
    assert isinstance(indicator, TechnicalIndicator)


def test_indicator_has_name():
    indicator = FakeEMAIndicator()
    assert indicator.name == "EMA"


def test_indicator_has_version():
    indicator = FakeEMAIndicator()
    assert indicator.version == "1.0.0"


def test_indicator_has_required_inputs():
    indicator = FakeEMAIndicator()
    assert "closes" in indicator.required_inputs


def test_compute_returns_output():
    indicator = FakeEMAIndicator()
    input_data = IndicatorInput(
        symbol="SPY", timeframe="1m",
        closes=[100, 101, 102, 103, 104],
    )
    result = indicator.compute(input_data)
    assert isinstance(result, IndicatorOutput)
    assert result.indicator_name == "EMA"
    assert result.symbol == "SPY"
    assert "ema" in result.values
    assert len(result.values["ema"]) == 5


def test_validate_params_returns_errors():
    indicator = FakeEMAIndicator()
    bad_params = IndicatorParams(period=0)
    errors = indicator.validate_params(bad_params)
    assert len(errors) > 0


def test_validate_params_valid():
    indicator = FakeEMAIndicator()
    good_params = IndicatorParams(period=20)
    errors = indicator.validate_params(good_params)
    assert len(errors) == 0


def test_indicator_params_has_defaults():
    """IndicatorParams has sensible defaults."""
    p = IndicatorParams()
    assert p.period == 14
    assert p.fast == 12
    assert p.slow == 26


def test_indicator_input_has_ohlcv_fields():
    """IndicatorInput has all OHLCV fields."""
    inp = IndicatorInput(symbol="SPY", timeframe="1m")
    assert hasattr(inp, "opens")
    assert hasattr(inp, "highs")
    assert hasattr(inp, "lows")
    assert hasattr(inp, "closes")
    assert hasattr(inp, "volumes")
    assert hasattr(inp, "timestamps")


def test_indicator_output_has_required_fields():
    """IndicatorOutput has name, symbol, timeframe, values."""
    out = IndicatorOutput(
        indicator_name="RSI", symbol="SPY", timeframe="1m",
        values={"rsi": [45.0, 50.0]},
    )
    assert out.indicator_name == "RSI"
    assert out.values["rsi"] == [45.0, 50.0]
