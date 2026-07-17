"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class WyckoffManifest:
    """Manifest for the Wyckoff AI."""
    agent_id: str = "raw-intelligence/technical-analysis.wyckoff"
    name: str = "Wyckoff AI"
    layer: str = "raw-intelligence/technical-analysis"
    description: str = "Detects Wyckoff accumulation/distribution phases."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "market:bar-closed",
    )
    publishes: tuple = (
        "ta:signal-emitted",
    )
    plugin_dependencies: tuple = (
        "patterns.wyckoff",
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = WyckoffManifest()
