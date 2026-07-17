"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class EscapeTopAgentManifest:
    agent_id: str = "technical-analysis.pattern.escape-top-agent"
    name: str = "Escape Top AI"
    division: str = "technical-analysis"
    team: str = "pattern"
    layer: str = "5-intelligence"
    description: str = 'Detects breakout-from-consolidation patterns.'
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
        # no plugin deps
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = EscapeTopAgentManifest()
