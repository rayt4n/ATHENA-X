"""Plugin manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class GammaExposureManifest:
    id: str = "options.gamma-exposure"
    name: str = "Gamma Exposure (GEX)"
    version: str = "0.1.0"
    type: str = "options"
    runtime: str = "python"
    inputs: tuple = ('option_chain', 'spot')
    params: dict = field(default_factory=dict)
    outputs: tuple = ('gex', 'gamma_flip')
    dependencies: tuple = ()


MANIFEST = GammaExposureManifest()
