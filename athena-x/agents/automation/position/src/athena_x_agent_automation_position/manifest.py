"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class PositionManifest:
    """Manifest for the Position AI."""
    agent_id: str = "automation.position"
    name: str = "Position AI"
    layer: str = "automation"
    description: str = "Position management (future). Disabled by feature flag. Reserved architecture per Change 16."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        # source agent — no subscriptions
    )
    publishes: tuple = (
        # sink agent — no publications
    )
    plugin_dependencies: tuple = (
        # no plugin dependencies
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = PositionManifest()
