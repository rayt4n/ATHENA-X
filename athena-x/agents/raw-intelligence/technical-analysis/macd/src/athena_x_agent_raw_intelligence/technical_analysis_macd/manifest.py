"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class MacdManifest:
    """Manifest for the MACD AI."""
    agent_id: str = "raw-intelligence/technical-analysis.macd"
    name: str = "MACD AI"
    layer: str = "raw-intelligence/technical-analysis"
    description: str = "Computes MACD and detects bullish/bearish crossovers."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "market:bar-closed",
    )
    publishes: tuple = (
        "ta:indicator-computed",
        "ta:signal-emitted",
    )
    plugin_dependencies: tuple = (
        "indicators.macd",
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = MacdManifest()
