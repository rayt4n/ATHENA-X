"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class GammaExposureAgentManifest:
    agent_id: str = "options-intelligence.gamma.gamma-exposure-agent"
    name: str = "Gamma Exposure AI"
    division: str = "options-intelligence"
    team: str = "gamma"
    layer: str = "5-intelligence"
    description: str = 'Computes GEX (gamma exposure).'
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
        "options.gamma-exposure",
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = GammaExposureAgentManifest()
