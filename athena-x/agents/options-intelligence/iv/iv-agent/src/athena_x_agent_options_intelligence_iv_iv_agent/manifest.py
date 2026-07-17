"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class IvAgentManifest:
    agent_id: str = "options-intelligence.iv.iv-agent"
    name: str = "IV AI"
    division: str = "options-intelligence"
    team: str = "iv"
    layer: str = "5-intelligence"
    description: str = "Computes implied volatility via Brent's method."
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
        "options.iv",
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = IvAgentManifest()
