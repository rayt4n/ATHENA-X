"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class RiskAgentManifest:
    agent_id: str = "automation.risk.risk-agent"
    name: str = "Risk AI"
    division: str = "automation"
    team: str = "risk"
    layer: str = "future"
    description: str = 'Pre-trade risk checks. Reserved — disabled by feature flag.'
    version: str = "0.1.0"
    subscribes_to: tuple = (
        # source agent
    )
    publishes: tuple = (
        # sink agent
    )
    plugin_dependencies: tuple = (
        # no plugin deps
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = RiskAgentManifest()
