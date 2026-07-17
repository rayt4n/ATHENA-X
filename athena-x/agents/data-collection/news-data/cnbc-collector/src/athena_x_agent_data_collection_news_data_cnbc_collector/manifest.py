"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class CnbcCollectorManifest:
    agent_id: str = "data-collection.news-data.cnbc-collector"
    name: str = "CNBC Collector"
    division: str = "data-collection"
    team: str = "news-data"
    layer: str = "1-provider-adapters"
    description: str = 'Ingests CNBC financial news.'
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


MANIFEST = CnbcCollectorManifest()
