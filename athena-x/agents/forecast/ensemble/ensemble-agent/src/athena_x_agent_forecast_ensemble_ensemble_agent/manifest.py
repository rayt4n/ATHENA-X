"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class EnsembleAgentManifest:
    agent_id: str = "forecast.ensemble.ensemble-agent"
    name: str = "Ensemble Forecast AI"
    division: str = "forecast"
    team: str = "ensemble"
    layer: str = "5-intelligence"
    description: str = 'Combines all model outputs using dynamic weights from Self-Correction Division.'
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "market:bar-closed",
    )
    publishes: tuple = (
        "forecast:trajectory-computed",
        "forecast:catalyst-detected",
    )
    plugin_dependencies: tuple = (
        # no plugin deps
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = EnsembleAgentManifest()
