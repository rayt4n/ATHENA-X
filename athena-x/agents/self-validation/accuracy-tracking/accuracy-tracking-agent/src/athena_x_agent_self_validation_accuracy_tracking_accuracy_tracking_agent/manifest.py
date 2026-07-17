"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class AccuracyTrackingAgentManifest:
    agent_id: str = "self-validation.accuracy-tracking.accuracy-tracking-agent"
    name: str = "Accuracy Tracking Agent"
    division: str = "self-validation"
    team: str = "accuracy-tracking"
    layer: str = "5-validation"
    description: str = 'Tracks rolling accuracy per model per regime.'
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


MANIFEST = AccuracyTrackingAgentManifest()
