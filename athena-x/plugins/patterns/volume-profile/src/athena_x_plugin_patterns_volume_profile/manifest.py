"""Plugin manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class VolumeProfileManifest:
    id: str = "patterns.volume-profile"
    name: str = "Volume Profile"
    version: str = "0.1.0"
    type: str = "pattern"
    runtime: str = "python"
    inputs: tuple = ('bars',)
    params: dict = field(default_factory=dict)
    outputs: tuple = ('poc', 'vah', 'val', 'profile')
    dependencies: tuple = ()


MANIFEST = VolumeProfileManifest()
