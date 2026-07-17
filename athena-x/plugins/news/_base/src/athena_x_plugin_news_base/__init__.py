"""NewsPlugin Protocol - stable interface for news category plugins."""
from .protocol import (
    NewsPlugin, NewsEvent, NewsCategory, NewsImpact,
    EventImportance, NarrativeDNA, CatalystEvent,
)

__all__ = [
    "NewsPlugin", "NewsEvent", "NewsCategory", "NewsImpact",
    "EventImportance", "NarrativeDNA", "CatalystEvent",
]
__version__ = "0.1.0"
