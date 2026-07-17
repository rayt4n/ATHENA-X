"""Tests for CrossMarketPlugin Protocol."""
import pytest
from athena_x_plugin_cross_market_base import (
    CrossMarketPlugin, MarketDataInput, CrossMarketOutput,
    CrossMarketCategory, MarketGroup,
)


class FakeCorrelationPlugin:
    @property
    def plugin_id(self): return "spy_es_correlation"
    @property
    def category(self): return CrossMarketCategory.CORRELATION
    @property
    def version(self): return "1.0.0"
    def compute(self, input_data):
        return CrossMarketOutput(
            plugin_id="spy_es_correlation",
            category=CrossMarketCategory.CORRELATION,
            value={"correlation": 0.98, "spy_leading": False},
        )


def test_protocol_is_runtime_checkable():
    plugin = FakeCorrelationPlugin()
    assert isinstance(plugin, CrossMarketPlugin)


def test_6_categories_defined():
    assert CrossMarketCategory.MARKET_MONITOR.value == "market_monitor"
    assert CrossMarketCategory.CORRELATION.value == "correlation"
    assert CrossMarketCategory.LEADERSHIP.value == "leadership"
    assert CrossMarketCategory.REGIME.value == "regime"
    assert CrossMarketCategory.ROTATION.value == "rotation"
    assert CrossMarketCategory.DIVERGENCE.value == "divergence"


def test_11_market_groups_defined():
    assert MarketGroup.CORE.value == "core"
    assert MarketGroup.VOLATILITY.value == "volatility"
    assert MarketGroup.SEMICONDUCTOR.value == "semiconductor"
    assert MarketGroup.MAG7.value == "mag7"
    assert MarketGroup.CRYPTO.value == "crypto"


def test_compute_returns_output():
    plugin = FakeCorrelationPlugin()
    inp = MarketDataInput(quotes={"SPY": {"last": 450}, "ES": {"last": 4520}})
    result = plugin.compute(inp)
    assert isinstance(result, CrossMarketOutput)
    assert result.value["correlation"] == 0.98
