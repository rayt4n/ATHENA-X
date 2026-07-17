"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class VwapManifest:
    """Manifest for the VWAP AI."""
    agent_id: str = "raw-intelligence/technical-analysis.vwap"
    name: str = "VWAP AI"
    layer: str = "raw-intelligence/technical-analysis"
    description: str = "Computes VWAP and detects deviations."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "market:bar-closed",
    )
    publishes: tuple = (
        "ta:indicator-computed",
        "ta:signal-emitted",
    )
    plugin_dependencies: tuple = (
        "indicators.vwap",
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = VwapManifest()
