"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ScenarioAnalysisManifest:
    """Manifest for the Scenario Analysis AI."""
    agent_id: str = "decision-intelligence.scenario-analysis"
    name: str = "Scenario Analysis AI"
    layer: str = "decision-intelligence"
    description: str = "Computes Bull/Base/Bear scenario probabilities based on regime + forecast + cross-market."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "forecast:trajectory-computed",
        "decision:regime-classified",
    )
    publishes: tuple = (
        "decision:scenario-updated",
    )
    plugin_dependencies: tuple = (
        # no plugin dependencies
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = ScenarioAnalysisManifest()
