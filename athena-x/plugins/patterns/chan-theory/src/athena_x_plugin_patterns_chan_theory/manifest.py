"""Plugin manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ChanTheoryManifest:
    id: str = "patterns.chan-theory"
    name: str = "Chan Theory (缠论) Analyzer"
    version: str = "0.1.0"
    type: str = "pattern"
    runtime: str = "python"
    inputs: tuple = ('bars',)
    params: dict = field(default_factory=dict)
    outputs: tuple = ('bi', 'duan', 'zhongshu')
    dependencies: tuple = ()


MANIFEST = ChanTheoryManifest()
