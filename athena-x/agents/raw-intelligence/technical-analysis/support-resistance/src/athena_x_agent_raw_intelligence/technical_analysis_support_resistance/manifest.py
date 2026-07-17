"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class SupportResistanceManifest:
    """Manifest for the Support/Resistance AI."""
    agent_id: str = "raw-intelligence/technical-analysis.support-resistance"
    name: str = "Support/Resistance AI"
    layer: str = "raw-intelligence/technical-analysis"
    description: str = "Identifies key support and resistance levels."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "market:bar-closed",
    )
    publishes: tuple = (
        "ta:level-identified",
    )
    plugin_dependencies: tuple = (
        # no plugin dependencies
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = SupportResistanceManifest()
