"""Plugin manifest — declares capabilities to the plugin-engine."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class StochasticManifest:
    id: str = "indicators.stochastic"
    name: str = "Stochastic Oscillator"
    version: str = "0.1.0"
    type: str = "indicator"
    runtime: str = "python"
    inputs: tuple = ('highs', 'lows', 'closes')
    params: dict = field(default_factory=lambda: {'k_period': 14, 'd_period': 3})
    outputs: tuple = ('k', 'd')
    dependencies: tuple = ()


MANIFEST = StochasticManifest()
