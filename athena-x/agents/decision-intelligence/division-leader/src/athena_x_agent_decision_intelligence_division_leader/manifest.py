"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class DivisionLeaderManifest:
    agent_id: str = "decision-intelligence.division-leader"
    name: str = "Decision Intelligence Division Leader"
    division: str = "decision-intelligence"
    team: str = "leadership"
    layer: str = "6-decision"
    description: str = 'Division leader for Decision Intelligence Division. Reports to Supervisor. Coordinates team leaders, handles division-level conflicts, reports division health metrics.'
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


MANIFEST = DivisionLeaderManifest()
