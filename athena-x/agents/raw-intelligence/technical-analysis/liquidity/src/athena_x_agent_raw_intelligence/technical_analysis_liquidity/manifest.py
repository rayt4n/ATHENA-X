"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class LiquidityManifest:
    """Manifest for the Liquidity AI."""
    agent_id: str = "raw-intelligence/technical-analysis.liquidity"
    name: str = "Liquidity AI"
    layer: str = "raw-intelligence/technical-analysis"
    description: str = "Detects liquidity pools and liquidity voids."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "market:bar-closed",
    )
    publishes: tuple = (
        "ta:level-identified",
    )
    plugin_dependencies: tuple = (
        # no plugin dependencies
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = LiquidityManifest()
