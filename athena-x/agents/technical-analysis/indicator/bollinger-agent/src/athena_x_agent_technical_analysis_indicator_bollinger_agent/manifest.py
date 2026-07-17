"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class BollingerAgentManifest:
    agent_id: str = "technical-analysis.indicator.bollinger-agent"
    name: str = "Bollinger AI"
    division: str = "technical-analysis"
    team: str = "indicator"
    layer: str = "5-intelligence"
    description: str = 'Bollinger Bands + squeeze/expansion detection.'
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
        "indicators.bollinger",
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = BollingerAgentManifest()
