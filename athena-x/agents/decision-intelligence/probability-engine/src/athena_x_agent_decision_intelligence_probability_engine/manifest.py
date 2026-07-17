"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ProbabilityEngineManifest:
    """Manifest for the Probability Engine."""
    agent_id: str = "decision-intelligence.probability-engine"
    name: str = "Probability Engine"
    layer: str = "decision-intelligence"
    description: str = "Monte Carlo simulation engine. Configurable DTE, simulations count, threshold."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "decision:volatility-projected",
        "forecast:trajectory-computed",
    )
    publishes: tuple = (
        "probability:simulation-run",
        "probability:profit-scored",
        "probability:strategy-matrix-updated",
    )
    plugin_dependencies: tuple = (
        # no plugin dependencies
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = ProbabilityEngineManifest()
