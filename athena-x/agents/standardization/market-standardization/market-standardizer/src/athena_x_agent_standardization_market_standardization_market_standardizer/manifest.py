"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class MarketStandardizerManifest:
    agent_id: str = "standardization.market-standardization.market-standardizer"
    name: str = "Market Standardizer Agent"
    division: str = "standardization"
    team: str = "market-standardization"
    layer: str = "3-standardization"
    description: str = 'Converts provider market data to canonical schema. close/Close/last/price → last_price. UTC timestamps. Normalized symbols, decimals, units. ONLY writer to market_db.'
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


MANIFEST = MarketStandardizerManifest()
