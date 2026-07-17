"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class TimeframeSyncAgentManifest:
    agent_id: str = "decision-intelligence.trade-timing.timeframe-sync-agent"
    name: str = "Timeframe Sync AI"
    division: str = "decision-intelligence"
    team: str = "trade-timing"
    layer: str = "6-decision"
    description: str = 'Multi-timeframe alignment: Monthly → Weekly → Daily → 4H → 1H → 30M → 15M → 5M → 1M → Alignment Score.'
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


MANIFEST = TimeframeSyncAgentManifest()
