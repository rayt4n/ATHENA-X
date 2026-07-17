"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class MultiTimeframeManifest:
    """Manifest for the Multi-Timeframe AI."""
    agent_id: str = "raw-intelligence/technical-analysis.multi-timeframe"
    name: str = "Multi-Timeframe AI"
    layer: str = "raw-intelligence/technical-analysis"
    description: str = "Analyzes trend alignment across 9 timeframes (Monthly→1M)."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "ta:indicator-computed",
    )
    publishes: tuple = (
        "ta:signal-emitted",
    )
    plugin_dependencies: tuple = (
        # no plugin dependencies
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = MultiTimeframeManifest()
