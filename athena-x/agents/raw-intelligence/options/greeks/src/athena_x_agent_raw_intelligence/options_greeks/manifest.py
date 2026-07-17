"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class GreeksManifest:
    """Manifest for the Greeks AI."""
    agent_id: str = "raw-intelligence/options.greeks"
    name: str = "Greeks AI"
    layer: str = "raw-intelligence/options"
    description: str = "Computes option Greeks (delta, gamma, theta, vega, rho)."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "market:quote-updated",
    )
    publishes: tuple = (
        "options:greeks-computed",
    )
    plugin_dependencies: tuple = (
        "options.greeks",
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = GreeksManifest()
