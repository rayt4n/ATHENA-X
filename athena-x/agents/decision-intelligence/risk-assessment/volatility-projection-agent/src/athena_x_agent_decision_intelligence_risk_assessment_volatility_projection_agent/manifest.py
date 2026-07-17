"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class VolatilityProjectionAgentManifest:
    agent_id: str = "decision-intelligence.risk-assessment.volatility-projection-agent"
    name: str = "Volatility Projection AI"
    division: str = "decision-intelligence"
    team: str = "risk-assessment"
    layer: str = "6-decision"
    description: str = 'Projects forward volatility using GARCH + ATR + IV term structure.'
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


MANIFEST = VolatilityProjectionAgentManifest()
