"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class AlphavantageCollectorManifest:
    agent_id: str = "data-collection.market-data.alphavantage-collector"
    name: str = "Alpha Vantage Collector"
    division: str = "data-collection"
    team: str = "market-data"
    layer: str = "1-provider-adapters"
    description: str = 'Downloads equity/ETF/currency data from Alpha Vantage.'
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


MANIFEST = AlphavantageCollectorManifest()
