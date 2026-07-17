"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class MoveManifest:
    """Manifest for the MOVE Cross-Market Agent."""
    agent_id: str = "raw-intelligence/cross-market.move"
    name: str = "MOVE Cross-Market Agent"
    layer: str = "raw-intelligence/cross-market"
    description: str = "ICE BofA MOVE Index (bond volatility). Feeds SPY Intelligence aggregator."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "market:quote-updated",
    )
    publishes: tuple = (
        "cross-market:symbol-state-updated",
    )
    plugin_dependencies: tuple = (
        # no plugin dependencies
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = MoveManifest()
