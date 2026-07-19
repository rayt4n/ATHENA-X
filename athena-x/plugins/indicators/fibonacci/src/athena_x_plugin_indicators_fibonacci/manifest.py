"""Plugin manifest — declares capabilities to the plugin-engine."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class FibonacciManifest:
    id: str = "indicators.fibonacci"
    name: str = "Fibonacci Retracement"
    version: str = "0.1.0"
    type: str = "indicator"
    runtime: str = "python"
    inputs: tuple = ('highs', 'lows')
    params: dict = field(default_factory=lambda: {'levels': [0.236, 0.382, 0.5, 0.618, 0.786]})
    outputs: tuple = ('levels',)
    dependencies: tuple = ()


MANIFEST = FibonacciManifest()
