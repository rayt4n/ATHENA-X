"""OptionsPlugin Protocol - stable interface for all options intelligence plugins.

Stage 8: Plugin-based architecture. Every metric is independently versioned + testable.
Metrics can be added, removed, enabled, disabled, or upgraded without affecting
the rest of the platform.

Optimized for SPY/ES/SPX 0DTE institutional-style trading.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol, runtime_checkable


class OptionsPluginCategory(str, Enum):
    """8 plugin categories."""
    VOLATILITY = "volatility"
    GREEKS = "greeks"
    DEALER = "dealer"
    FLOW = "flow"
    OPEN_INTEREST = "open_interest"
    ZERO_DTE = "0dte"
    DARK_POOL = "dark_pool"
    PROBABILITY = "probability"


@dataclass
class OptionsPluginConfig:
    """Configuration for an options plugin."""
    symbol: str = "SPY"
    refresh_interval_seconds: int = 5
    custom: dict[str, Any] = field(default_factory=dict)


@dataclass
class OptionsPluginInput:
    """Input data for an options plugin computation."""
    symbol: str
    spot_price: float
    # Option chain data (from canonical_options DB)
    chain: list[dict] = field(default_factory=list)
    # Historical IV data (for IV Rank, IV Percentile)
    iv_history: list[float] = field(default_factory=list)
    # Open interest data
    oi_by_strike: dict[float, dict] = field(default_factory=dict)
    # Volume data
    volume_by_strike: dict[float, dict] = field(default_factory=dict)
    # Dark pool prints
    dark_pool_prints: list[dict] = field(default_factory=list)
    # Option flow
    option_flow: list[dict] = field(default_factory=list)
    # Greeks (from greeks plugins)
    greeks: dict[str, dict] = field(default_factory=dict)
    # Timestamp
    timestamp: str = ""


@dataclass
class OptionsPluginOutput:
    """Output of an options plugin computation."""
    plugin_id: str
    symbol: str
    category: OptionsPluginCategory
    value: Any  # metric-specific value
    confidence: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)
    calculation_time_ms: float = 0.0


@runtime_checkable
class OptionsPlugin(Protocol):
    """Stable interface for all options intelligence plugins.

    Every options metric plugin implements this protocol.
    New metrics can be added without changing any consumer code.

    Usage:
        plugin: OptionsPlugin = GammaFlipPlugin()
        result = plugin.compute(input_data, config)
    """

    @property
    def plugin_id(self) -> str:
        """Plugin ID (e.g., 'gamma_flip', 'iv_rank', 'max_pain')."""
        ...

    @property
    def category(self) -> OptionsPluginCategory:
        """Plugin category."""
        ...

    @property
    def version(self) -> str:
        """Plugin version (semver)."""
        ...

    def compute(
        self,
        input_data: OptionsPluginInput,
        config: OptionsPluginConfig | None = None,
    ) -> OptionsPluginOutput:
        """Compute the options metric.

        Args:
            input_data: option chain + market data
            config: plugin configuration

        Returns:
            OptionsPluginOutput with the computed metric.
        """
        ...
