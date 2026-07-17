"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ChanTheoryManifest:
    """Manifest for the Chan Theory AI."""
    agent_id: str = "raw-intelligence/technical-analysis.chan-theory"
    name: str = "Chan Theory AI"
    layer: str = "raw-intelligence/technical-analysis"
    description: str = "缠论分析 (Bi/Duan/Zhongshu detection)."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "market:bar-closed",
    )
    publishes: tuple = (
        "ta:signal-emitted",
    )
    plugin_dependencies: tuple = (
        "patterns.chan-theory",
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = ChanTheoryManifest()
