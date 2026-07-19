"""Plugin manifest — declares capabilities to the plugin-engine."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class CciManifest:
    id: str = "indicators.cci"
    name: str = "Commodity Channel Index"
    version: str = "0.1.0"
    type: str = "indicator"
    runtime: str = "python"
    inputs: tuple = ('highs', 'lows', 'closes')
    params: dict = field(default_factory=lambda: {'period': 20})
    outputs: tuple = ('value',)
    dependencies: tuple = ()


MANIFEST = CciManifest()
