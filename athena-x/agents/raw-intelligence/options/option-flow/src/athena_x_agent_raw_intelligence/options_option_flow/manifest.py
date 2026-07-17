"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class OptionFlowManifest:
    """Manifest for the Option Flow AI."""
    agent_id: str = "raw-intelligence/options.option-flow"
    name: str = "Option Flow AI"
    layer: str = "raw-intelligence/options"
    description: str = "Detects unusual options activity."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "market:trade-printed",
    )
    publishes: tuple = (
        "options:unusual-activity",
    )
    plugin_dependencies: tuple = (
        # no plugin dependencies
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = OptionFlowManifest()
