"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class SmartMoneyManifest:
    """Manifest for the Smart Money AI."""
    agent_id: str = "raw-intelligence/technical-analysis.smart-money"
    name: str = "Smart Money AI"
    layer: str = "raw-intelligence/technical-analysis"
    description: str = "Detects order blocks, FVGs, and smart money footprints."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "market:bar-closed",
    )
    publishes: tuple = (
        "ta:signal-emitted",
    )
    plugin_dependencies: tuple = (
        "patterns.smart-money",
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = SmartMoneyManifest()
