"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class BrokerAgentManifest:
    agent_id: str = "automation.broker.broker-agent"
    name: str = "Broker API Adapter"
    division: str = "automation"
    team: str = "broker"
    layer: str = "future"
    description: str = 'Broker API integration (IBKR, Alpaca). Reserved — disabled by feature flag.'
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


MANIFEST = BrokerAgentManifest()
