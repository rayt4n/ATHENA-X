"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class BrokerManifest:
    """Manifest for the Broker API Adapter."""
    agent_id: str = "automation.broker"
    name: str = "Broker API Adapter"
    layer: str = "automation"
    description: str = "Broker API integration (IBKR, Alpaca). Disabled by feature flag. Reserved architecture per Change 16."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        # source agent — no subscriptions
    )
    publishes: tuple = (
        # sink agent — no publications
    )
    plugin_dependencies: tuple = (
        # no plugin dependencies
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = BrokerManifest()
