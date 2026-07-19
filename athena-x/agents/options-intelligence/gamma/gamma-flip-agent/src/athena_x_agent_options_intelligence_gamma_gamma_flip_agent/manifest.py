"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class GammaFlipAgentManifest:
    agent_id: str = "options-intelligence.gamma.gamma-flip-agent"
    name: str = "Gamma Flip AI"
    division: str = "options-intelligence"
    team: str = "gamma"
    layer: str = "5-intelligence"
    description: str = 'Detects gamma flip transitions.'
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
        # no plugin deps
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = GammaFlipAgentManifest()
