"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class SpyIntelligenceAggregatorManifest:
    agent_id: str = "decision-intelligence.scenario-analysis.spy-intelligence-aggregator"
    name: str = "SPY Intelligence Aggregator"
    division: str = "decision-intelligence"
    team: str = "scenario-analysis"
    layer: str = "6-decision"
    description: str = 'Subscribes to all 20 cross-market collectors. Aggregates their state into a unified SPY Intelligence view.'
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "cross-market:symbol-state-updated",
    )
    publishes: tuple = (
        "cross-market:spy-intelligence-updated",
    )
    plugin_dependencies: tuple = (
        # no plugin deps
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = SpyIntelligenceAggregatorManifest()
