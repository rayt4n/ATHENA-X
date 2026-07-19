"""Tests for OptionsPlugin Protocol."""
import pytest
from athena_x_plugin_options_base import (
    OptionsPlugin, OptionsPluginInput, OptionsPluginOutput,
    OptionsPluginCategory, OptionsPluginConfig,
)


class FakeGammaFlipPlugin:
    """Test implementation."""
    @property
    def plugin_id(self): return "gamma_flip"
    @property
    def category(self): return OptionsPluginCategory.DEALER
    @property
    def version(self): return "1.0.0"
    def compute(self, input_data, config=None):
        return OptionsPluginOutput(
            plugin_id="gamma_flip", symbol=input_data.symbol,
            category=OptionsPluginCategory.DEALER,
            value={"gamma_flip": 4520.0, "dealer_gamma": "long"},
        )


def test_protocol_is_runtime_checkable():
    plugin = FakeGammaFlipPlugin()
    assert isinstance(plugin, OptionsPlugin)


def test_8_categories_defined():
    assert OptionsPluginCategory.VOLATILITY.value == "volatility"
    assert OptionsPluginCategory.GREEKS.value == "greeks"
    assert OptionsPluginCategory.DEALER.value == "dealer"
    assert OptionsPluginCategory.FLOW.value == "flow"
    assert OptionsPluginCategory.OPEN_INTEREST.value == "open_interest"
    assert OptionsPluginCategory.ZERO_DTE.value == "0dte"
    assert OptionsPluginCategory.DARK_POOL.value == "dark_pool"
    assert OptionsPluginCategory.PROBABILITY.value == "probability"


def test_input_has_all_data_fields():
    inp = OptionsPluginInput(symbol="SPY", spot_price=450.0)
    assert hasattr(inp, "chain")
    assert hasattr(inp, "iv_history")
    assert hasattr(inp, "oi_by_strike")
    assert hasattr(inp, "volume_by_strike")
    assert hasattr(inp, "dark_pool_prints")
    assert hasattr(inp, "option_flow")
    assert hasattr(inp, "greeks")


def test_output_has_required_fields():
    out = OptionsPluginOutput(
        plugin_id="iv_rank", symbol="SPY",
        category=OptionsPluginCategory.VOLATILITY,
        value=67.5,
    )
    assert out.plugin_id == "iv_rank"
    assert out.confidence == 1.0


def test_compute_returns_output():
    plugin = FakeGammaFlipPlugin()
    inp = OptionsPluginInput(symbol="SPY", spot_price=450.0)
    result = plugin.compute(inp)
    assert isinstance(result, OptionsPluginOutput)
    assert result.value["gamma_flip"] == 4520.0
