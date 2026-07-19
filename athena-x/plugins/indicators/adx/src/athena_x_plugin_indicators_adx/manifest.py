"""Plugin manifest — declares capabilities to the plugin-engine."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class AdxManifest:
    id: str = "indicators.adx"
    name: str = "Average Directional Index"
    version: str = "0.1.0"
    type: str = "indicator"
    runtime: str = "python"
    inputs: tuple = ('highs', 'lows', 'closes')
    params: dict = field(default_factory=lambda: {'period': 14})
    outputs: tuple = ('adx', 'plus_di', 'minus_di')
    dependencies: tuple = ()


MANIFEST = AdxManifest()
