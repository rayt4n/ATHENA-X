"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class AlertEngineAgentManifest:
    agent_id: str = "dashboard-reporting.alert-engine.alert-engine-agent"
    name: str = "Alert Engine Agent"
    division: str = "dashboard-reporting"
    team: str = "alert-engine"
    layer: str = "7-reporting"
    description: str = 'Fires alerts on configurable conditions: signal conflicts, regime changes, unusual activity, threshold breaches.'
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


MANIFEST = AlertEngineAgentManifest()
