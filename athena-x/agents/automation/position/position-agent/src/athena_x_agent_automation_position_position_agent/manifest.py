"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class PositionAgentManifest:
    agent_id: str = "automation.position.position-agent"
    name: str = "Position AI"
    division: str = "automation"
    team: str = "position"
    layer: str = "future"
    description: str = 'Position management. Reserved — disabled by feature flag.'
    version: str = "0.1.0"
    subscribes_to: tuple = (
        # source agent
    )
    publishes: tuple = (
        # sink agent
    )
    plugin_dependencies: tuple = (
        # no plugin deps
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = PositionAgentManifest()
