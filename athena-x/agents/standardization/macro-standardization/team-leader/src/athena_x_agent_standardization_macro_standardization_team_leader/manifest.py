"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class TeamLeaderManifest:
    agent_id: str = "standardization.macro-standardization.team-leader"
    name: str = "Macro Standardization Team Leader"
    division: str = "standardization"
    team: str = "macro-standardization"
    layer: str = "3-standardization"
    description: str = 'Team leader for Macro Standardization Team in Standardization Division. Reports to division leader. Coordinates agents in the team, handles team-level conflicts, reports team health.'
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "*",
    )
    publishes: tuple = (
        "supervisor:agent-failing",
        "supervisor:retry-requested",
    )
    plugin_dependencies: tuple = (
        # no plugin deps
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = TeamLeaderManifest()
