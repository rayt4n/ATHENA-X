"""Plugin manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class MaxPainManifest:
    id: str = "options.max-pain"
    name: str = "Max Pain Calculator"
    version: str = "0.1.0"
    type: str = "options"
    runtime: str = "python"
    inputs: tuple = ('option_chain',)
    params: dict = field(default_factory=dict)
    outputs: tuple = ('max_pain',)
    dependencies: tuple = ()


MANIFEST = MaxPainManifest()
