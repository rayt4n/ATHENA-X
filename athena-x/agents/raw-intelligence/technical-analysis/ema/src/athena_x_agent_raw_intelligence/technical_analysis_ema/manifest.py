"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class EmaManifest:
    """Manifest for the EMA AI."""
    agent_id: str = "raw-intelligence/technical-analysis.ema"
    name: str = "EMA AI"
    layer: str = "raw-intelligence/technical-analysis"
    description: str = "Computes EMA values and detects crossovers."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "market:bar-closed",
    )
    publishes: tuple = (
        "ta:indicator-computed",
        "ta:signal-emitted",
    )
    plugin_dependencies: tuple = (
        "indicators.ema",
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = EmaManifest()
