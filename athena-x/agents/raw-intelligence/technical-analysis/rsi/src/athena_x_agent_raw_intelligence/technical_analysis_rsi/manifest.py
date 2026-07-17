"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class RsiManifest:
    """Manifest for the RSI AI."""
    agent_id: str = "raw-intelligence/technical-analysis.rsi"
    name: str = "RSI AI"
    layer: str = "raw-intelligence/technical-analysis"
    description: str = "Computes RSI and detects overbought/oversold conditions."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "market:bar-closed",
    )
    publishes: tuple = (
        "ta:indicator-computed",
        "ta:signal-emitted",
    )
    plugin_dependencies: tuple = (
        "indicators.rsi",
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = RsiManifest()
