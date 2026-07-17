"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ModelComparisonAgentManifest:
    agent_id: str = "self-validation.model-comparison.model-comparison-agent"
    name: str = "Model Comparison Agent"
    division: str = "self-validation"
    team: str = "model-comparison"
    layer: str = "5-validation"
    description: str = 'A/B compares models. Identifies winners per market context.'
    version: str = "0.1.0"
    subscribes_to: tuple = (
        # source agent
    )
    publishes: tuple = (
        "learning:prediction-scored",
        "learning:weight-adjusted",
    )
    plugin_dependencies: tuple = (
        # no plugin deps
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = ModelComparisonAgentManifest()
