"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class VolumeProfileManifest:
    """Manifest for the Volume Profile AI."""
    agent_id: str = "raw-intelligence/technical-analysis.volume-profile"
    name: str = "Volume Profile AI"
    layer: str = "raw-intelligence/technical-analysis"
    description: str = "Computes POC/VAH/VAL and volume distribution."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "market:bar-closed",
    )
    publishes: tuple = (
        "ta:level-identified",
        "ta:signal-emitted",
    )
    plugin_dependencies: tuple = (
        "patterns.volume-profile",
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = VolumeProfileManifest()
