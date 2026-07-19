"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class TeamLeaderManifest:
    agent_id: str = "self-validation.self-correction.team-leader"
    name: str = "Self-Correction Team Leader"
    division: str = "self-validation"
    team: str = "self-correction"
    layer: str = "5-validation"
    description: str = 'Team leader for Self-Correction Team in Self-Validation Division. Reports to division leader. Coordinates agents in the team, handles team-level conflicts, reports team health.'
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
