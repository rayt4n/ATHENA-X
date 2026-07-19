"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class WeeklyReportAgentManifest:
    agent_id: str = "dashboard-reporting.weekly-report.weekly-report-agent"
    name: str = "Weekly Report Agent"
    division: str = "dashboard-reporting"
    team: str = "weekly-report"
    layer: str = "7-reporting"
    description: str = 'Generates comprehensive weekly reports. Long horizon, deep analysis.'
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


MANIFEST = WeeklyReportAgentManifest()
