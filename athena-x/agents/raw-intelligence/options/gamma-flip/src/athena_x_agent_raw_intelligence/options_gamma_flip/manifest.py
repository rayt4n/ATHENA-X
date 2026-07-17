"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class GammaFlipManifest:
    """Manifest for the Gamma Flip AI."""
    agent_id: str = "raw-intelligence/options.gamma-flip"
    name: str = "Gamma Flip AI"
    layer: str = "raw-intelligence/options"
    description: str = "Detects gamma flip transitions."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "options:gamma-exposure-updated",
    )
    publishes: tuple = (
        "options:gamma-exposure-updated",
    )
    plugin_dependencies: tuple = (
        # no plugin dependencies
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = GammaFlipManifest()
