"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class MaxPainAgentManifest:
    agent_id: str = "options-intelligence.max-pain.max-pain-agent"
    name: str = "Max Pain AI"
    division: str = "options-intelligence"
    team: str = "max-pain"
    layer: str = "5-intelligence"
    description: str = 'Computes max pain for each expiry.'
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
        "options.max-pain",
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = MaxPainAgentManifest()
