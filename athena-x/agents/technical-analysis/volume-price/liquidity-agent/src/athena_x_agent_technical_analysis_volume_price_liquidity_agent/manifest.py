"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class LiquidityAgentManifest:
    agent_id: str = "technical-analysis.volume-price.liquidity-agent"
    name: str = "Liquidity AI"
    division: str = "technical-analysis"
    team: str = "volume-price"
    layer: str = "5-intelligence"
    description: str = 'Detects liquidity pools and liquidity voids.'
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "market:bar-closed",
    )
    publishes: tuple = (
        "ta:indicator-computed",
        "ta:signal-emitted",
        "ta:level-identified",
    )
    plugin_dependencies: tuple = (
        # no plugin deps
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = LiquidityAgentManifest()
