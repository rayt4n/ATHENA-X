"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class GeopoliticsAgentManifest:
    agent_id: str = "macro-intelligence.geopolitics.geopolitics-agent"
    name: str = "Geopolitics AI"
    division: str = "macro-intelligence"
    team: str = "geopolitics"
    layer: str = "5-intelligence"
    description: str = 'Geopolitical events + market impact assessment.'
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


MANIFEST = GeopoliticsAgentManifest()
