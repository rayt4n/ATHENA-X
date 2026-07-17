"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class TrendManifest:
    """Manifest for the Trend AI."""
    agent_id: str = "raw-intelligence/technical-analysis.trend"
    name: str = "Trend AI"
    layer: str = "raw-intelligence/technical-analysis"
    description: str = "Detects trend direction and strength using ADX + price action."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "market:bar-closed",
    )
    publishes: tuple = (
        "ta:signal-emitted",
        "ta:level-identified",
    )
    plugin_dependencies: tuple = (
        "indicators.adx",
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = TrendManifest()
