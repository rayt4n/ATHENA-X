"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class PredictionAuditAgentManifest:
    agent_id: str = "self-validation.prediction-audit.prediction-audit-agent"
    name: str = "Prediction Audit Agent"
    division: str = "self-validation"
    team: str = "prediction-audit"
    layer: str = "5-validation"
    description: str = 'Audits each forecast against actual outcome. Records errors.'
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


MANIFEST = PredictionAuditAgentManifest()
