"""Plugin manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class GreeksManifest:
    id: str = "options.greeks"
    name: str = "Greeks Calculator"
    version: str = "0.1.0"
    type: str = "options"
    runtime: str = "python"
    inputs: tuple = ('spot', 'strike', 'expiry', 'iv', 'rate')
    params: dict = field(default_factory=dict)
    outputs: tuple = ('delta', 'gamma', 'theta', 'vega', 'rho')
    dependencies: tuple = ()


MANIFEST = GreeksManifest()
