"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class AtrManifest:
    """Manifest for the ATR AI."""
    agent_id: str = "raw-intelligence/technical-analysis.atr"
    name: str = "ATR AI"
    layer: str = "raw-intelligence/technical-analysis"
    description: str = "Computes ATR for volatility measurement."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "market:bar-closed",
    )
    publishes: tuple = (
        "ta:indicator-computed",
    )
    plugin_dependencies: tuple = (
        "indicators.atr",
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = AtrManifest()
