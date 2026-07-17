"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class SmartMoneyAgentManifest:
    agent_id: str = "technical-analysis.volume-price.smart-money-agent"
    name: str = "Smart Money AI"
    division: str = "technical-analysis"
    team: str = "volume-price"
    layer: str = "5-intelligence"
    description: str = 'Detects order blocks, FVGs, and smart money footprints.'
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "market:bar-closed",
    )
    publishes: tuple = (
        "ta:indicator-computed",
        "ta:signal-emitted",
        "ta:level-identified",
    )
    plugin_dependencies: tuple = (
        "patterns.smart-money",
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = SmartMoneyAgentManifest()
