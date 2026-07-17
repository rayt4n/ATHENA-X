"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class VolatilityProjectionManifest:
    """Manifest for the Volatility Projection AI."""
    agent_id: str = "decision-intelligence.volatility-projection"
    name: str = "Volatility Projection AI"
    layer: str = "decision-intelligence"
    description: str = "Projects forward volatility using GARCH + ATR + IV term structure."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "ta:indicator-computed",
        "options:iv-updated",
    )
    publishes: tuple = (
        "decision:volatility-projected",
    )
    plugin_dependencies: tuple = (
        # no plugin dependencies
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = VolatilityProjectionManifest()
