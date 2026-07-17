"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class AiConsensusAgentManifest:
    agent_id: str = "decision-intelligence.scenario-analysis.ai-consensus-agent"
    name: str = "AI Consensus AI"
    division: str = "decision-intelligence"
    team: str = "scenario-analysis"
    layer: str = "6-decision"
    description: str = 'Aggregates all decision agents into single consensus view per symbol.'
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


MANIFEST = AiConsensusAgentManifest()
