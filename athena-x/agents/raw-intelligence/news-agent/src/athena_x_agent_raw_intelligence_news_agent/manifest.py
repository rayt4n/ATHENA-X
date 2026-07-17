"""Agent manifest."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class NewsAgentManifest:
    """Manifest for the News Agent."""
    agent_id: str = "raw-intelligence.news-agent"
    name: str = "News Agent"
    layer: str = "raw-intelligence"
    description: str = "Ingests news from RSS + provider APIs. Runs HuggingFace FinBERT for sentiment + impact."
    version: str = "0.1.0"
    subscribes_to: tuple = (
        # source agent — no subscriptions
    )
    publishes: tuple = (
        "news:headline-received",
        "news:sentiment-scored",
        "news:impact-classified",
        "news:entity-mentioned",
    )
    plugin_dependencies: tuple = (
        # no plugin dependencies
    )
    capabilities: dict = field(default_factory=lambda: {
        "multi_instance": True,
        "headless": True,
        "default_hotkey": "",
    })


MANIFEST = NewsAgentManifest()
