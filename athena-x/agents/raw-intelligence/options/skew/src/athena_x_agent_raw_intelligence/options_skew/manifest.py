"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class SkewManifest:
    """Manifest for the Skew AI."""
    agent_id: str = "raw-intelligence/options.skew"
    name: str = "Skew AI"
    layer: str = "raw-intelligence/options"
    description: str = "Analyzes IV skew (risk reversal, butterfly)."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "options:iv-updated",
    )
    publishes: tuple = (
        "options:iv-updated",
    )
    plugin_dependencies: tuple = (
        "options.skew",
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = SkewManifest()
