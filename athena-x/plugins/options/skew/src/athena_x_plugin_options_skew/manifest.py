"""Plugin manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class SkewManifest:
    id: str = "options.skew"
    name: str = "IV Skew Calculator"
    version: str = "0.1.0"
    type: str = "options"
    runtime: str = "python"
    inputs: tuple = ('iv_chain',)
    params: dict = field(default_factory=dict)
    outputs: tuple = ('skew', 'risk_reversal', 'butterfly')
    dependencies: tuple = ()


MANIFEST = SkewManifest()
