"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class PullUpPatternManifest:
    """Manifest for the Pull-Up Pattern AI."""
    agent_id: str = "raw-intelligence/technical-analysis.pull-up-pattern"
    name: str = "Pull-Up Pattern AI"
    layer: str = "raw-intelligence/technical-analysis"
    description: str = "Detects pull-up continuation patterns."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "market:bar-closed",
    )
    publishes: tuple = (
        "ta:signal-emitted",
    )
    plugin_dependencies: tuple = (
        # no plugin dependencies
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = PullUpPatternManifest()
