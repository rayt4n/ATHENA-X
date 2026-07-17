"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ExpectedMoveManifest:
    """Manifest for the Expected Move AI."""
    agent_id: str = "raw-intelligence/options.expected-move"
    name: str = "Expected Move AI"
    layer: str = "raw-intelligence/options"
    description: str = "Computes expected move from options market."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "options:iv-updated",
    )
    publishes: tuple = (
        "decision:expected-move-updated",
    )
    plugin_dependencies: tuple = (
        # no plugin dependencies
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = ExpectedMoveManifest()
