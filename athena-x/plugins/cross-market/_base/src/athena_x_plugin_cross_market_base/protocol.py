"""CrossMarketPlugin Protocol - stable interface for all cross-market plugins.

Stage 9: Every cross-market metric is an independent plugin.
The engine doesn't know which correlations or leadership signals exist.
It only loads plugins.

Categories:
  - market_monitor: one per asset (spy, es, vix, dxy, ...)
  - correlation: SPY<->ES, SPY<->VIX, ...
  - leadership: who is leading? who is lagging?
  - regime: Risk-On, Risk-Off, Inflation, ...
  - rotation: Tech->Defensive, Growth->Value, ...
  - divergence: spy_es_divergence, vix_not_confirming, ...
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol, runtime_checkable


class CrossMarketCategory(str, Enum):
    MARKET_MONITOR = "market_monitor"
    CORRELATION = "correlation"
    LEADERSHIP = "leadership"
    REGIME = "regime"
    ROTATION = "rotation"
    DIVERGENCE = "divergence"


class MarketGroup(str, Enum):
    CORE = "core"
    VOLATILITY = "volatility"
    RATES = "rates"
    CURRENCY = "currency"
    COMMODITIES = "commodities"
    BREADTH = "breadth"
    SECTORS = "sectors"
    SEMICONDUCTOR = "semiconductor"
    MAG7 = "mag7"
    GLOBAL = "global"
    CRYPTO = "crypto"


@dataclass
class MarketDataInput:
    """Input data for a cross-market plugin."""
    symbol: str = ""
    # Latest quotes for all monitored symbols
    quotes: dict[str, dict] = field(default_factory=dict)  # symbol -> {last, change_pct, volume, ...}
    # Recent returns for correlation calculation
    returns: dict[str, list[float]] = field(default_factory=dict)  # symbol -> [ret1, ret2, ...]
    # Timestamp
    timestamp: str = ""


@dataclass
class CrossMarketOutput:
    """Output of a cross-market plugin computation."""
    plugin_id: str
    category: CrossMarketCategory
    value: Any
    confidence: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)
    calculation_time_ms: float = 0.0


@runtime_checkable
class CrossMarketPlugin(Protocol):
    """Stable interface for all cross-market intelligence plugins.

    Usage:
        plugin: CrossMarketPlugin = SPYCorrelationPlugin()
        result = plugin.compute(input_data)
    """

    @property
    def plugin_id(self) -> str: ...

    @property
    def category(self) -> CrossMarketCategory: ...

    @property
    def version(self) -> str: ...

    def compute(self, input_data: MarketDataInput) -> CrossMarketOutput: ...
