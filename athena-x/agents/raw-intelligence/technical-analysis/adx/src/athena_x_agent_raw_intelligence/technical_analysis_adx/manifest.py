"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class AdxManifest:
    """Manifest for the ADX AI."""
    agent_id: str = "raw-intelligence/technical-analysis.adx"
    name: str = "ADX AI"
    layer: str = "raw-intelligence/technical-analysis"
    description: str = "Computes ADX and detects trend strength."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "market:bar-closed",
    )
    publishes: tuple = (
        "ta:indicator-computed",
        "ta:signal-emitted",
    )
    plugin_dependencies: tuple = (
        "indicators.adx",
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = AdxManifest()
