"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ElliottWaveAgentManifest:
    agent_id: str = "technical-analysis.pattern.elliott-wave-agent"
    name: str = "Elliott Wave AI"
    division: str = "technical-analysis"
    team: str = "pattern"
    layer: str = "5-intelligence"
    description: str = 'Analyzes Elliott Wave patterns.'
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
        "patterns.elliott-wave",
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = ElliottWaveAgentManifest()
