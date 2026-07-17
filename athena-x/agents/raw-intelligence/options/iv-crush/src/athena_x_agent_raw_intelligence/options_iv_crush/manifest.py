"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class IvCrushManifest:
    """Manifest for the IV Crush AI."""
    agent_id: str = "raw-intelligence/options.iv-crush"
    name: str = "IV Crush AI"
    layer: str = "raw-intelligence/options"
    description: str = "Detects IV crush events post-earnings."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "options:iv-updated",
    )
    publishes: tuple = (
        "options:iv-updated",
    )
    plugin_dependencies: tuple = (
        # no plugin dependencies
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = IvCrushManifest()
