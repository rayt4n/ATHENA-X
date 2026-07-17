"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class TradingEconomicsCollectorManifest:
    agent_id: str = "data-collection.macro-data.trading-economics-collector"
    name: str = "Trading Economics Collector"
    division: str = "data-collection"
    team: str = "macro-data"
    layer: str = "1-provider-adapters"
    description: str = 'Downloads global macro indicators from Trading Economics.'
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


MANIFEST = TradingEconomicsCollectorManifest()
