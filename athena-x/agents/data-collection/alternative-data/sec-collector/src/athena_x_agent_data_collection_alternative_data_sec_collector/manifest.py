"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class SecCollectorManifest:
    agent_id: str = "data-collection.alternative-data.sec-collector"
    name: str = "SEC Collector"
    division: str = "data-collection"
    team: str = "alternative-data"
    layer: str = "1-provider-adapters"
    description: str = 'Downloads SEC EDGAR filings (13F, 10-K, 10-Q, 8-K).'
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


MANIFEST = SecCollectorManifest()
