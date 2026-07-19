"""Plugin manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class VolatilitySurfaceManifest:
    id: str = "options.volatility-surface"
    name: str = "Volatility Surface Builder"
    version: str = "0.1.0"
    type: str = "options"
    runtime: str = "python"
    inputs: tuple = ('option_chain',)
    params: dict = field(default_factory=dict)
    outputs: tuple = ('surface',)
    dependencies: tuple = ()


MANIFEST = VolatilitySurfaceManifest()
