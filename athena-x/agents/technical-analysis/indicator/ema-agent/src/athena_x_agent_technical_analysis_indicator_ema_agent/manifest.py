"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class EmaAgentManifest:
    agent_id: str = "technical-analysis.indicator.ema-agent"
    name: str = "EMA AI"
    division: str = "technical-analysis"
    team: str = "indicator"
    layer: str = "5-intelligence"
    description: str = 'Exponential Moving Average + crossover detection.'
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
        "indicators.ema",
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = EmaAgentManifest()
