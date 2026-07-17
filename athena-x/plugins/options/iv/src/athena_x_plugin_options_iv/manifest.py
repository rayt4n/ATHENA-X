"""Plugin manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class IvManifest:
    id: str = "options.iv"
    name: str = "Implied Volatility Solver"
    version: str = "0.1.0"
    type: str = "options"
    runtime: str = "python"
    inputs: tuple = ('spot', 'strike', 'expiry', 'option_price', 'type')
    params: dict = field(default_factory=dict)
    outputs: tuple = ('iv',)
    dependencies: tuple = ()


MANIFEST = IvManifest()
