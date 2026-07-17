"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class BollingerManifest:
    """Manifest for the Bollinger AI."""
    agent_id: str = "raw-intelligence/technical-analysis.bollinger"
    name: str = "Bollinger AI"
    layer: str = "raw-intelligence/technical-analysis"
    description: str = "Computes Bollinger Bands and detects squeeze/expansion."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "market:bar-closed",
    )
    publishes: tuple = (
        "ta:indicator-computed",
        "ta:signal-emitted",
    )
    plugin_dependencies: tuple = (
        "indicators.bollinger",
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = BollingerManifest()
