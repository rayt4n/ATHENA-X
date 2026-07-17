"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class FredCollectorManifest:
    agent_id: str = "data-collection.macro-data.fred-collector"
    name: str = "FRED Collector"
    division: str = "data-collection"
    team: str = "macro-data"
    layer: str = "1-provider-adapters"
    description: str = 'Downloads US Treasury yields + economic indicators from FRED.'
    version: str = "0.1.0"
    subscribes_to: tuple = (
        # source agent
    )
    publishes: tuple = (
        # sink agent
    )
    plugin_dependencies: tuple = (
        # no plugin deps
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = FredCollectorManifest()
