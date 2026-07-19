"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class PolymarketCollectorManifest:
    agent_id: str = "data-collection.alternative-data.polymarket-collector"
    name: str = "Polymarket Collector"
    division: str = "data-collection"
    team: str = "alternative-data"
    layer: str = "1-provider-adapters"
    description: str = 'Downloads prediction market probabilities from Polymarket.'
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


MANIFEST = PolymarketCollectorManifest()
