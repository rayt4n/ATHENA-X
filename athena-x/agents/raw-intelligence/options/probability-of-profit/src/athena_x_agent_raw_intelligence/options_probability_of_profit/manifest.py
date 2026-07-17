"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ProbabilityOfProfitManifest:
    """Manifest for the Probability of Profit AI."""
    agent_id: str = "raw-intelligence/options.probability-of-profit"
    name: str = "Probability of Profit AI"
    layer: str = "raw-intelligence/options"
    description: str = "Computes PoP for option strategies."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "options:iv-updated",
    )
    publishes: tuple = (
        "probability:profit-scored",
    )
    plugin_dependencies: tuple = (
        # no plugin dependencies
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = ProbabilityOfProfitManifest()
