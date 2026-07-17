"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class WyckoffAgentManifest:
    agent_id: str = "technical-analysis.wyckoff.wyckoff-agent"
    name: str = "Wyckoff AI"
    division: str = "technical-analysis"
    team: str = "wyckoff"
    layer: str = "5-intelligence"
    description: str = 'Detects Wyckoff accumulation/distribution phases.'
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
        "patterns.wyckoff",
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = WyckoffAgentManifest()
