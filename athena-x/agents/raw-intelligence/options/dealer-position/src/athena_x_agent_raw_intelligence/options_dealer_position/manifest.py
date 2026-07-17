"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class DealerPositionManifest:
    """Manifest for the Dealer Position AI."""
    agent_id: str = "raw-intelligence/options.dealer-position"
    name: str = "Dealer Position AI"
    layer: str = "raw-intelligence/options"
    description: str = "Estimates dealer positioning."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "options:greeks-computed",
    )
    publishes: tuple = (
        "options:greeks-computed",
    )
    plugin_dependencies: tuple = (
        # no plugin dependencies
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = DealerPositionManifest()
