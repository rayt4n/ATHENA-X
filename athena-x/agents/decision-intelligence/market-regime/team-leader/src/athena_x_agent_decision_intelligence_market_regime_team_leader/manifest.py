"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class TeamLeaderManifest:
    agent_id: str = "decision-intelligence.market-regime.team-leader"
    name: str = "Market Regime Team Leader"
    division: str = "decision-intelligence"
    team: str = "market-regime"
    layer: str = "6-decision"
    description: str = 'Team leader for Market Regime Team in Decision Intelligence Division. Reports to division leader. Coordinates agents in the team, handles team-level conflicts, reports team health.'
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
