"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class GreeksAgentManifest:
    agent_id: str = "options-intelligence.greeks.greeks-agent"
    name: str = "Greeks AI"
    division: str = "options-intelligence"
    team: str = "greeks"
    layer: str = "5-intelligence"
    description: str = 'Computes option Greeks (delta, gamma, theta, vega, rho).'
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "market:bar-closed",
    )
    publishes: tuple = (
        "options:iv-updated",
        "options:greeks-computed",
        "options:chain-refreshed",
        "options:gamma-exposure-updated",
        "options:max-pain-updated",
        "options:unusual-activity",
    )
    plugin_dependencies: tuple = (
        "options.greeks",
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = GreeksAgentManifest()
