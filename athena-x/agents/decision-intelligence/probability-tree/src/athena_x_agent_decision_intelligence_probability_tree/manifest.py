"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ProbabilityTreeManifest:
    """Manifest for the Probability Tree AI."""
    agent_id: str = "decision-intelligence.probability-tree"
    name: str = "Probability Tree AI"
    layer: str = "decision-intelligence"
    description: str = "Builds a probability tree of future states (price paths + regime transitions)."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "decision:regime-classified",
        "forecast:trajectory-computed",
    )
    publishes: tuple = (
        "decision:probability-tree-updated",
    )
    plugin_dependencies: tuple = (
        # no plugin dependencies
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = ProbabilityTreeManifest()
