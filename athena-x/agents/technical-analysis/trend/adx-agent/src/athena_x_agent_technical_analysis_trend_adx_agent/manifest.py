"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class AdxAgentManifest:
    agent_id: str = "technical-analysis.trend.adx-agent"
    name: str = "ADX AI"
    division: str = "technical-analysis"
    team: str = "trend"
    layer: str = "5-intelligence"
    description: str = 'Computes ADX and detects trend strength.'
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
        "indicators.adx",
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = AdxAgentManifest()
