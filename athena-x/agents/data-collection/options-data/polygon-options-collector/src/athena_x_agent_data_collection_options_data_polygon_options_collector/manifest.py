"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class PolygonOptionsCollectorManifest:
    agent_id: str = "data-collection.options-data.polygon-options-collector"
    name: str = "Polygon Options Collector"
    division: str = "data-collection"
    team: str = "options-data"
    layer: str = "1-provider-adapters"
    description: str = 'Downloads options chains from Polygon.'
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


MANIFEST = PolygonOptionsCollectorManifest()
