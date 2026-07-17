"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class VolatilitySurfaceManifest:
    """Manifest for the Volatility Surface AI."""
    agent_id: str = "raw-intelligence/options.volatility-surface"
    name: str = "Volatility Surface AI"
    layer: str = "raw-intelligence/options"
    description: str = "Builds 3D IV surface across strikes/expiries."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "options:iv-updated",
    )
    publishes: tuple = (
        "options:iv-updated",
    )
    plugin_dependencies: tuple = (
        "options.volatility-surface",
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = VolatilitySurfaceManifest()
