"""Plugin manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ElliottWaveManifest:
    id: str = "patterns.elliott-wave"
    name: str = "Elliott Wave Analyzer"
    version: str = "0.1.0"
    type: str = "pattern"
    runtime: str = "python"
    inputs: tuple = ('bars',)
    params: dict = field(default_factory=dict)
    outputs: tuple = ('waves', 'current_pattern')
    dependencies: tuple = ()


MANIFEST = ElliottWaveManifest()
