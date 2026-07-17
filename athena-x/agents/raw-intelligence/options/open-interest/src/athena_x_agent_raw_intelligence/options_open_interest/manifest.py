"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class OpenInterestManifest:
    """Manifest for the Open Interest AI."""
    agent_id: str = "raw-intelligence/options.open-interest"
    name: str = "Open Interest AI"
    layer: str = "raw-intelligence/options"
    description: str = "Analyzes OI changes and concentrations."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "market:quote-updated",
    )
    publishes: tuple = (
        "options:chain-refreshed",
    )
    plugin_dependencies: tuple = (
        # no plugin dependencies
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = OpenInterestManifest()
