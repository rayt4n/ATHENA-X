"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class OptionsValidatorAgentManifest:
    agent_id: str = "validation.options-validator.options-validator-agent"
    name: str = "Options Validator Agent"
    division: str = "validation"
    team: str = "options-validator"
    layer: str = "2-validation"
    description: str = 'IV/Greeks/OI consistency checks. Put-call parity verification.'
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


MANIFEST = OptionsValidatorAgentManifest()
