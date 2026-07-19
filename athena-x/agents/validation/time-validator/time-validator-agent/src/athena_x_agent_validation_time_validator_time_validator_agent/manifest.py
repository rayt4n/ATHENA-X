"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class TimeValidatorAgentManifest:
    agent_id: str = "validation.time-validator.time-validator-agent"
    name: str = "Time Validator Agent"
    division: str = "validation"
    team: str = "time-validator"
    layer: str = "2-validation"
    description: str = 'Timestamp normalization + staleness detection. Rejects out-of-order events.'
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


MANIFEST = TimeValidatorAgentManifest()
