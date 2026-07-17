"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class SmaManifest:
    """Manifest for the SMA AI."""
    agent_id: str = "raw-intelligence/technical-analysis.sma"
    name: str = "SMA AI"
    layer: str = "raw-intelligence/technical-analysis"
    description: str = "Computes SMA values and detects crossovers."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "market:bar-closed",
    )
    publishes: tuple = (
        "ta:indicator-computed",
        "ta:signal-emitted",
    )
    plugin_dependencies: tuple = (
        "indicators.sma",
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = SmaManifest()
