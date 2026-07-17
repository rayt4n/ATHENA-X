"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class AiConsensusManifest:
    """Manifest for the AI Consensus AI."""
    agent_id: str = "decision-intelligence.ai-consensus"
    name: str = "AI Consensus AI"
    layer: str = "decision-intelligence"
    description: str = "Aggregates all decision agents into a single consensus view per symbol."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "decision:regime-classified",
        "decision:scenario-updated",
        "decision:expected-move-updated",
        "decision:probability-tree-updated",
        "decision:timeframe-alignment-updated",
    )
    publishes: tuple = (
        "decision:ai-consensus-updated",
    )
    plugin_dependencies: tuple = (
        # no plugin dependencies
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = AiConsensusManifest()
