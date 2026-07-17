"""NewsPlugin Protocol + Narrative DNA + Catalyst Radar types.

Stage 10: Every news category is a plugin. The engine classifies, correlates,
and produces a single Narrative DNA for downstream AI.

The 4th intelligence object (after Technical DNA, Options DNA, Market DNA):
  Narrative DNA = { primary_driver, secondary_driver, theme, confidence, ... }
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Protocol, runtime_checkable


class NewsCategory(str, Enum):
    BREAKING = "breaking"
    ECONOMIC = "economic"
    FED = "fed"
    TREASURY = "treasury"
    EARNINGS = "earnings"
    GEOPOLITICAL = "geopolitical"
    ENERGY = "energy"
    SEMICONDUCTOR = "semiconductor"
    REGULATORY = "regulatory"
    ALTERNATIVE = "alternative"


class EventImportance(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class NewsEvent:
    """Structured market event (canonical schema)."""
    event_id: str
    timestamp: datetime
    source: str
    headline: str
    category: NewsCategory
    subcategory: str = ""
    symbols: list[str] = field(default_factory=list)
    region: str = ""
    market: str = ""
    importance: EventImportance = EventImportance.MEDIUM
    confidence: float = 0.8
    related_assets: list[str] = field(default_factory=list)
    status: str = "active"  # active, stale, resolved
    summary: str = ""
    url: str = ""
    raw_content: str | None = None
    sentiment: float | None = None  # filled by NLP (Stage 10 does NOT compute this)


@dataclass
class NewsImpact:
    """Directional market impact of an event (not a forecast)."""
    event_id: str
    impact_chain: list[dict] = field(default_factory=list)
    # e.g., [{"asset": "Bonds", "direction": "up"}, {"asset": "DXY", "direction": "up"}, ...]
    probability: float = 0.5
    confidence: float = 0.7


@dataclass
class NarrativeDNA:
    """The 4th intelligence object - Market Narrative DNA.

    Consumed by Stage 11 (Forecast), Stage 12 (Probability),
    Stage 13 (Supervisor), Stage 15 (Reports).
    """
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Primary narrative
    primary_driver: str = "unknown"
    secondary_driver: str | None = None
    current_theme: str = "unknown"  # Inflation Risk, Growth, Geopolitical, etc.
    confidence: float = 0.0

    # Supporting evidence
    supporting_evidence: list[str] = field(default_factory=list)

    # Event timeline (today)
    event_timeline: list[dict] = field(default_factory=list)

    # Market impact summary
    impact_summary: dict[str, str] = field(default_factory=dict)  # asset -> direction

    # Story of the day
    story_of_the_day: str = ""

    # Upcoming catalysts
    upcoming_catalysts: list[dict] = field(default_factory=list)

    # Active events
    active_events: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "primary_driver": self.primary_driver,
            "secondary_driver": self.secondary_driver,
            "current_theme": self.current_theme,
            "confidence": round(self.confidence, 4),
            "supporting_evidence": self.supporting_evidence,
            "event_timeline": self.event_timeline,
            "impact_summary": self.impact_summary,
            "story_of_the_day": self.story_of_the_day,
            "upcoming_catalysts": self.upcoming_catalysts,
            "active_events": self.active_events,
        }


@dataclass
class CatalystEvent:
    """An upcoming market-moving event."""
    event_id: str
    name: str
    scheduled_time: datetime
    category: NewsCategory
    importance: EventImportance
    symbols: list[str] = field(default_factory=list)
    description: str = ""
    time_horizon: str = "today"  # "15min", "1hour", "today", "this_week"


@runtime_checkable
class NewsPlugin(Protocol):
    """Stable interface for news category plugins."""

    @property
    def plugin_id(self) -> str: ...

    @property
    def category(self) -> NewsCategory: ...

    @property
    def version(self) -> str: ...

    def classify(self, raw_article: dict) -> NewsEvent: ...

    def assess_impact(self, event: NewsEvent) -> NewsImpact: ...
