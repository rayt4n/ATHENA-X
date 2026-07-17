"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class SelfCorrectionAgentManifest:
    """Manifest for the Self-Correction Agent."""
    agent_id: str = "self-correction.self-correction-agent"
    name: str = "Self-Correction Agent"
    layer: str = "self-correction"
    description: str = "Continuous learning engine (Change 12). Pipeline: prediction → market outcome → compare → error → weight adjustment → improve model. Every prediction is scored. Adjusts model_weights table."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        "forecast:trajectory-computed",
        "market:bar-closed",
    )
    publishes: tuple = (
        "learning:prediction-scored",
        "learning:weight-adjusted",
    )
    plugin_dependencies: tuple = (
        # no plugin dependencies
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = SelfCorrectionAgentManifest()
