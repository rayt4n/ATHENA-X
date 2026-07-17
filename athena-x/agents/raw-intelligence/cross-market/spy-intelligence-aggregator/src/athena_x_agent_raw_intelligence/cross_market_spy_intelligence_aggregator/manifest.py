"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class SpyIntelligenceAggregatorManifest:
    """Manifest for the SPY Intelligence Aggregator."""
    agent_id: str = "raw-intelligence/cross-market.spy-intelligence-aggregator"
    name: str = "SPY Intelligence Aggregator"
    layer: str = "raw-intelligence/cross-market"
    description: str = "Subscribes to all 20 cross-market agents. Aggregates their state into a unified SPY Intelligence view. This is the single source of truth for SPY context."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "cross-market:symbol-state-updated",
    )
    publishes: tuple = (
        "cross-market:spy-intelligence-updated",
    )
    plugin_dependencies: tuple = (
        # no plugin dependencies
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = SpyIntelligenceAggregatorManifest()
