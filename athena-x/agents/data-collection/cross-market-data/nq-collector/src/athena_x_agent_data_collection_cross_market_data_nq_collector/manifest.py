"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class NqCollectorManifest:
    agent_id: str = "data-collection.cross-market-data.nq-collector"
    name: str = "NQ Cross-Market Collector"
    division: str = "data-collection"
    team: str = "cross-market-data"
    layer: str = "1-provider-adapters"
    description: str = 'Downloads E-mini Nasdaq 100 Futures from the best available provider. Feeds Cross-Market Intelligence.'
    version: str = "0.1.0"
    subscribes_to: tuple = (
        # source agent
    )
    publishes: tuple = (
        "cross-market:symbol-state-updated",
    )
    plugin_dependencies: tuple = (
        # no plugin deps
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = NqCollectorManifest()
