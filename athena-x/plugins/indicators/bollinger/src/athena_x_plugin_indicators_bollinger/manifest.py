"""Plugin manifest — declares capabilities to the plugin-engine."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class BollingerManifest:
    id: str = "indicators.bollinger"
    name: str = "Bollinger Bands"
    version: str = "0.1.0"
    type: str = "indicator"
    runtime: str = "python"
    inputs: tuple = ('closes',)
    params: dict = field(default_factory=lambda: {'period': 20, 'std_dev': 2})
    outputs: tuple = ('upper', 'middle', 'lower', 'percent_b')
    dependencies: tuple = ()


MANIFEST = BollingerManifest()
