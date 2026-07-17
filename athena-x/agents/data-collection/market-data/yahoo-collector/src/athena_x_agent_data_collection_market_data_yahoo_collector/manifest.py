"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class YahooCollectorManifest:
    agent_id: str = "data-collection.market-data.yahoo-collector"
    name: str = "Yahoo Collector"
    division: str = "data-collection"
    team: str = "market-data"
    layer: str = "1-provider-adapters"
    description: str = 'Downloads equity/ETF/index data from Yahoo Finance.'
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


MANIFEST = YahooCollectorManifest()
