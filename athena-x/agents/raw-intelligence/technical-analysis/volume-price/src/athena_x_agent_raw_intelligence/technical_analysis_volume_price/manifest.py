"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class VolumePriceManifest:
    """Manifest for the Volume Price AI."""
    agent_id: str = "raw-intelligence/technical-analysis.volume-price"
    name: str = "Volume Price AI"
    layer: str = "raw-intelligence/technical-analysis"
    description: str = "Analyzes volume-price relationships."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "market:bar-closed",
    )
    publishes: tuple = (
        "ta:signal-emitted",
    )
    plugin_dependencies: tuple = (
        "indicators.obv",
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = VolumePriceManifest()
