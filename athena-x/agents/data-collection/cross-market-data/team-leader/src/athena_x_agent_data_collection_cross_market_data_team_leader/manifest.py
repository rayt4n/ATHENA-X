"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class TeamLeaderManifest:
    agent_id: str = "data-collection.cross-market-data.team-leader"
    name: str = "Cross-Market Data Team Leader"
    division: str = "data-collection"
    team: str = "cross-market-data"
    layer: str = "1-provider-adapters"
    description: str = 'Team leader for Cross-Market Data Team in Data Collection Division. Reports to division leader. Coordinates agents in the team, handles team-level conflicts, reports team health.'
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
