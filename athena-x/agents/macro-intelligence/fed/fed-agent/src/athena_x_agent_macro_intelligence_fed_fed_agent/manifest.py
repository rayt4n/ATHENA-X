"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class FedAgentManifest:
    agent_id: str = "macro-intelligence.fed.fed-agent"
    name: str = "Fed AI"
    division: str = "macro-intelligence"
    team: str = "fed"
    layer: str = "5-intelligence"
    description: str = 'Federal Reserve: funds rate, FOMC decisions, balance sheet.'
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "market:bar-closed",
    )
    publishes: tuple = (
        "macro:indicator-released",
        "macro:yield-curve-updated",
        "macro:fx-rate-updated",
        "macro:commodity-updated",
    )
    plugin_dependencies: tuple = (
        # no plugin deps
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = FedAgentManifest()
