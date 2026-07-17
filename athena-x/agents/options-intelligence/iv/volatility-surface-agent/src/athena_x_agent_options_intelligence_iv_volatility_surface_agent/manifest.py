"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class VolatilitySurfaceAgentManifest:
    agent_id: str = "options-intelligence.iv.volatility-surface-agent"
    name: str = "Volatility Surface AI"
    division: str = "options-intelligence"
    team: str = "iv"
    layer: str = "5-intelligence"
    description: str = 'Builds 3D IV surface across strikes/expiries.'
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
        "options.volatility-surface",
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = VolatilitySurfaceAgentManifest()
