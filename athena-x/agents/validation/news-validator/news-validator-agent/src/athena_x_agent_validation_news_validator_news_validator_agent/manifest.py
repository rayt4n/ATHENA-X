"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class NewsValidatorAgentManifest:
    agent_id: str = "validation.news-validator.news-validator-agent"
    name: str = "News Validator Agent"
    division: str = "validation"
    team: str = "news-validator"
    layer: str = "2-validation"
    description: str = 'Duplicate detection + source reputation ranking. Filters manipulation.'
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


MANIFEST = NewsValidatorAgentManifest()
