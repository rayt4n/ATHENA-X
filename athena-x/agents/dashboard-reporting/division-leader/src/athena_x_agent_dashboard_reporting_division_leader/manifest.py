"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class DivisionLeaderManifest:
    agent_id: str = "dashboard-reporting.division-leader"
    name: str = "Dashboard & Reporting Division Leader"
    division: str = "dashboard-reporting"
    team: str = "leadership"
    layer: str = "7-reporting"
    description: str = 'Division leader for Dashboard & Reporting Division. Reports to Supervisor. Coordinates team leaders, handles division-level conflicts, reports division health metrics.'
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
