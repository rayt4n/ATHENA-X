"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class _0DteManifest:
    """Manifest for the 0DTE AI."""
    agent_id: str = "raw-intelligence/options.0dte"
    name: str = "0DTE AI"
    layer: str = "raw-intelligence/options"
    description: str = "Specialized analysis for 0-days-to-expiry options."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "options:chain-refreshed",
    )
    publishes: tuple = (
        "options:unusual-activity",
    )
    plugin_dependencies: tuple = (
        # no plugin dependencies
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = _0DteManifest()
