"""Plugin manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class WyckoffManifest:
    id: str = "patterns.wyckoff"
    name: str = "Wyckoff Method Analyzer"
    version: str = "0.1.0"
    type: str = "pattern"
    runtime: str = "python"
    inputs: tuple = ('bars', 'volume')
    params: dict = field(default_factory=dict)
    outputs: tuple = ('phase', 'events')
    dependencies: tuple = ()


MANIFEST = WyckoffManifest()
