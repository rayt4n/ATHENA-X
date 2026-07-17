"""Plugin manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class CandlestickManifest:
    id: str = "patterns.candlestick"
    name: str = "Candlestick Pattern Recognition"
    version: str = "0.1.0"
    type: str = "pattern"
    runtime: str = "python"
    inputs: tuple = ('bars',)
    params: dict = field(default_factory=dict)
    outputs: tuple = ('patterns',)
    dependencies: tuple = ()


MANIFEST = CandlestickManifest()
