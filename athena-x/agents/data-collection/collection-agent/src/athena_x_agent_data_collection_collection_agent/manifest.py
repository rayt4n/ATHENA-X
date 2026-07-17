"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class CollectionAgentManifest:
    """Manifest for the Data Collection Agent."""
    agent_id: str = "data-collection.collection-agent"
    name: str = "Data Collection Agent"
    layer: str = "data-collection"
    description: str = "Pulls data from providers (Yahoo → Finnhub → Polygon → FlashAlpha → FRED → AlphaVantage failover chain). Normalizes timestamps. Writes raw payloads to raw_market_data schema."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        # source agent — no subscriptions
    )
    publishes: tuple = (
        "market:quote-updated",
        "market:trade-printed",
        "market:level2-updated",
        "market:bar-closed",
        "market:provider-failed-over",
    )
    plugin_dependencies: tuple = (
        # no plugin dependencies
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = CollectionAgentManifest()
