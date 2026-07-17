"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ProbabilityTreeAgentManifest:
    agent_id: str = "decision-intelligence.probability.probability-tree-agent"
    name: str = "Probability Tree AI"
    division: str = "decision-intelligence"
    team: str = "probability"
    layer: str = "6-decision"
    description: str = 'Builds probability tree of future states.'
    version: str = "0.1.0"
    subscribes_to: tuple = (
        # source agent
    )
    publishes: tuple = (
        "decision:regime-classified",
        "decision:scenario-updated",
        "decision:expected-move-updated",
        "decision:volatility-projected",
        "decision:probability-tree-updated",
        "decision:ai-consensus-updated",
        "decision:timeframe-alignment-updated",
        "probability:simulation-run",
    )
    plugin_dependencies: tuple = (
        # no plugin deps
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = ProbabilityTreeAgentManifest()
