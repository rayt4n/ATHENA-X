"""Plugin manifest — declares capabilities to the plugin-engine."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class IchimokuManifest:
    id: str = "indicators.ichimoku"
    name: str = "Ichimoku Cloud"
    version: str = "0.1.0"
    type: str = "indicator"
    runtime: str = "python"
    inputs: tuple = ('highs', 'lows', 'closes')
    params: dict = field(default_factory=lambda: {})
    outputs: tuple = ('tenkan', 'kijun', 'senkou_a', 'senkou_b', 'chikou')
    dependencies: tuple = ()


MANIFEST = IchimokuManifest()
