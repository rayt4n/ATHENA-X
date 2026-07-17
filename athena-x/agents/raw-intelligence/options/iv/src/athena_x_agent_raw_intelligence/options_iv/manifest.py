"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class IvManifest:
    """Manifest for the IV AI."""
    agent_id: str = "raw-intelligence/options.iv"
    name: str = "IV AI"
    layer: str = "raw-intelligence/options"
    description: str = "Computes implied volatility via Brent's method."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "market:quote-updated",
    )
    publishes: tuple = (
        "options:iv-updated",
    )
    plugin_dependencies: tuple = (
        "options.iv",
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = IvManifest()
