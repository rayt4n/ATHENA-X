"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class VolumeValidatorAgentManifest:
    agent_id: str = "validation.volume-validator.volume-validator-agent"
    name: str = "Volume Validator Agent"
    division: str = "validation"
    team: str = "volume-validator"
    layer: str = "2-validation"
    description: str = 'Volume sanity checks. Detects impossible spikes or zero-volume anomalies.'
    version: str = "0.1.0"
    subscribes_to: tuple = (
        # source agent
    )
    publishes: tuple = (
        # sink agent
    )
    plugin_dependencies: tuple = (
        # no plugin deps
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = VolumeValidatorAgentManifest()
