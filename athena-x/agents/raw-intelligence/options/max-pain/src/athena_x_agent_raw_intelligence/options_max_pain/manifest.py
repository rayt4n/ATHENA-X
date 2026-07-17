"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class MaxPainManifest:
    """Manifest for the Max Pain AI."""
    agent_id: str = "raw-intelligence/options.max-pain"
    name: str = "Max Pain AI"
    layer: str = "raw-intelligence/options"
    description: str = "Computes max pain for each expiry."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "market:quote-updated",
    )
    publishes: tuple = (
        "options:max-pain-updated",
    )
    plugin_dependencies: tuple = (
        "options.max-pain",
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = MaxPainManifest()
