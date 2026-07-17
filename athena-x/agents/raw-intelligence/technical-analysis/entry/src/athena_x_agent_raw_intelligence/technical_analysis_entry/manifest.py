"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class EntryManifest:
    """Manifest for the Entry AI."""
    agent_id: str = "raw-intelligence/technical-analysis.entry"
    name: str = "Entry AI"
    layer: str = "raw-intelligence/technical-analysis"
    description: str = "Identifies high-probability entry points."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "ta:signal-emitted",
        "ta:level-identified",
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


MANIFEST = EntryManifest()
