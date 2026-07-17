"""Plugin manifest — declares capabilities to the plugin-engine."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ObvManifest:
    id: str = "indicators.obv"
    name: str = "On-Balance Volume"
    version: str = "0.1.0"
    type: str = "indicator"
    runtime: str = "python"
    inputs: tuple = ('closes', 'volumes')
    params: dict = field(default_factory=lambda: {})
    outputs: tuple = ('value',)
    dependencies: tuple = ()


MANIFEST = ObvManifest()
