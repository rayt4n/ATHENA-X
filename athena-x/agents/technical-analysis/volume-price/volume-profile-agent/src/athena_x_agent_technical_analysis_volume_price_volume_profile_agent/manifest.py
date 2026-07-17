"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class VolumeProfileAgentManifest:
    agent_id: str = "technical-analysis.volume-price.volume-profile-agent"
    name: str = "Volume Profile AI"
    division: str = "technical-analysis"
    team: str = "volume-price"
    layer: str = "5-intelligence"
    description: str = 'Computes POC/VAH/VAL and volume distribution.'
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "market:bar-closed",
    )
    publishes: tuple = (
        "ta:indicator-computed",
        "ta:signal-emitted",
        "ta:level-identified",
    )
    plugin_dependencies: tuple = (
        "patterns.volume-profile",
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = VolumeProfileAgentManifest()
