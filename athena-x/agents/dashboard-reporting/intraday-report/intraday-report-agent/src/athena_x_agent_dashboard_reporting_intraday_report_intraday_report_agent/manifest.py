"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class IntradayReportAgentManifest:
    agent_id: str = "dashboard-reporting.intraday-report.intraday-report-agent"
    name: str = "Intraday Report Agent"
    division: str = "dashboard-reporting"
    team: str = "intraday-report"
    layer: str = "7-reporting"
    description: str = 'Generates intraday snapshots every 15 minutes during market hours.'
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


MANIFEST = IntradayReportAgentManifest()
