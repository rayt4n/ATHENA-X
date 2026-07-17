"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ElliottWaveManifest:
    """Manifest for the Elliott Wave AI."""
    agent_id: str = "raw-intelligence/technical-analysis.elliott-wave"
    name: str = "Elliott Wave AI"
    layer: str = "raw-intelligence/technical-analysis"
    description: str = "Analyzes Elliott Wave patterns."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "market:bar-closed",
    )
    publishes: tuple = (
        "ta:signal-emitted",
    )
    plugin_dependencies: tuple = (
        "patterns.elliott-wave",
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = ElliottWaveManifest()
