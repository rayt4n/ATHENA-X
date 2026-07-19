"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ChanTheoryAgentManifest:
    agent_id: str = "technical-analysis.chan-theory.chan-theory-agent"
    name: str = "Chan Theory AI"
    division: str = "technical-analysis"
    team: str = "chan-theory"
    layer: str = "5-intelligence"
    description: str = '缠论分析 (Bi/Duan/Zhongshu detection).'
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
        "patterns.chan-theory",
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = ChanTheoryAgentManifest()
