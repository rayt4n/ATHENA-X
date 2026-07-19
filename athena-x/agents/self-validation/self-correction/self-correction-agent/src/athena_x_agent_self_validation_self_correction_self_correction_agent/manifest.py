"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class SelfCorrectionAgentManifest:
    agent_id: str = "self-validation.self-correction.self-correction-agent"
    name: str = "Self-Correction Agent"
    division: str = "self-validation"
    team: str = "self-correction"
    layer: str = "5-validation"
    description: str = 'Adjusts model weights based on accuracy tracking. Updates ai_memory_db + model_weights table.'
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


MANIFEST = SelfCorrectionAgentManifest()
