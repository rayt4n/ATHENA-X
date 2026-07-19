"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class NewsStandardizerManifest:
    agent_id: str = "standardization.news-standardization.news-standardizer"
    name: str = "News Standardizer Agent"
    division: str = "standardization"
    team: str = "news-standardization"
    layer: str = "3-standardization"
    description: str = 'Converts provider news to canonical schema. ONLY writer to news_db.'
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


MANIFEST = NewsStandardizerManifest()
