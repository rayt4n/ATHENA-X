"""Plugin manifest — declares capabilities to the plugin-engine."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class EmaManifest:
    id: str = "indicators.ema"
    name: str = "Exponential Moving Average"
    version: str = "0.1.0"
    type: str = "indicator"
    runtime: str = "python"
    inputs: tuple = ('closes',)
    params: dict = field(default_factory=lambda: {'period': 20})
    outputs: tuple = ('value', 'signal')
    dependencies: tuple = ()


MANIFEST = EmaManifest()
