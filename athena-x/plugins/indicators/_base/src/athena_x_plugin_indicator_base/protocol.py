"""TechnicalIndicator Protocol - the stable interface for all indicators.

This is the contract that every indicator plugin implements. New indicators
can be added without changing any consumer code.

Stage 5.1: Plugin architecture - stable interface from day one.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass
class IndicatorParams:
    """Parameters for an indicator computation."""
    period: int = 14
    fast: int = 12
    slow: int = 26
    signal: int = 9
    std_dev: float = 2.0
    custom: dict[str, Any] = field(default_factory=dict)


@dataclass
class IndicatorInput:
    """Input data for an indicator computation."""
    symbol: str
    timeframe: str
    opens: list[float] = field(default_factory=list)
    highs: list[float] = field(default_factory=list)
    lows: list[float] = field(default_factory=list)
    closes: list[float] = field(default_factory=list)
    volumes: list[int] = field(default_factory=list)
    timestamps: list[int] = field(default_factory=list)  # unix-millis


@dataclass
class IndicatorOutput:
    """Output of an indicator computation."""
    indicator_name: str
    symbol: str
    timeframe: str
    values: dict[str, list[float]]  # e.g., {"ema": [450.1, 450.2, ...]}
    signals: list[str] = field(default_factory=list)  # e.g., ["bullish_crossover"]
    metadata: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class TechnicalIndicator(Protocol):
    """Stable interface for all technical indicators.

    Every indicator plugin implements this protocol. New indicators can be
    added without changing any consumer code.

    Usage:
        indicator: TechnicalIndicator = EMAIndicator()
        result = indicator.compute(input_data, params)
    """

    @property
    def name(self) -> str:
        """Indicator name (e.g., 'EMA', 'RSI', 'MACD')."""
        ...

    @property
    def version(self) -> str:
        """Indicator version (semver)."""
        ...

    @property
    def required_inputs(self) -> list[str]:
        """Required input fields (e.g., ['closes', 'volumes'])."""
        ...

    def compute(
        self,
        input_data: IndicatorInput,
        params: IndicatorParams | None = None,
    ) -> IndicatorOutput:
        """Compute the indicator value(s).

        Args:
            input_data: OHLCV data for the symbol
            params: indicator parameters (period, fast/slow, etc.)

        Returns:
            IndicatorOutput with computed values + any signals detected.
        """
        ...

    def validate_params(self, params: IndicatorParams) -> list[str]:
        """Validate parameters. Returns list of error messages (empty if valid)."""
        ...
