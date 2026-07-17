"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class LiveDashboardAgentManifest:
    agent_id: str = "dashboard-reporting.live-dashboard.live-dashboard-agent"
    name: str = "Live Dashboard Agent"
    division: str = "dashboard-reporting"
    team: str = "live-dashboard"
    layer: str = "7-reporting"
    description: str = 'Pushes real-time updates to the frontend via WebSocket. Subscribes to all events the dashboard needs.'
    version: str = "0.1.0"
    subscribes_to: tuple = (
        # source agent
    )
    publishes: tuple = (
        "report:generation-started",
        "report:generation-completed",
        "report:exported",
        "report:stored",
    )
    plugin_dependencies: tuple = (
        # no plugin deps
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = LiveDashboardAgentManifest()
