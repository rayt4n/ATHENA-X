"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class TimeframeSyncManifest:
    """Manifest for the Timeframe Synchronization AI."""
    agent_id: str = "decision-intelligence.timeframe-sync"
    name: str = "Timeframe Synchronization AI"
    layer: str = "decision-intelligence"
    description: str = "Computes multi-timeframe alignment score (Change 10): Monthly → Weekly → Daily → 4H → 1H → 30M → 15M → 5M → 1M → Alignment Score."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "ta:indicator-computed",
    )
    publishes: tuple = (
        "decision:timeframe-alignment-updated",
    )
    plugin_dependencies: tuple = (
        # no plugin dependencies
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = TimeframeSyncManifest()
