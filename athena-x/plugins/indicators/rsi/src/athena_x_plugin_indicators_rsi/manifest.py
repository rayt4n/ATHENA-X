"""Plugin manifest — declares capabilities to the plugin-engine."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class RsiManifest:
    id: str = "indicators.rsi"
    name: str = "Relative Strength Index"
    version: str = "0.1.0"
    type: str = "indicator"
    runtime: str = "python"
    inputs: tuple = ('closes',)
    params: dict = field(default_factory=lambda: {'period': 14})
    outputs: tuple = ('value', 'signal')
    dependencies: tuple = ()


MANIFEST = RsiManifest()
