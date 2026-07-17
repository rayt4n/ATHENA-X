#!/usr/bin/env python3
"""
STEP 4 Stage 10 - Market Narrative Intelligence Platform
==========================================================
Implements:
  1. plugins/news/_base/ - NewsPlugin Protocol
  2. 10+ news category manifests
  3. engines/narrative-engine/ - Event Classification + Impact + Timeline + Narrative
  4. agents/narrative-intelligence/ - Narrative DNA Agent + Catalyst Radar Agent
  5. runtime/stage10-integration/ - acceptance tests

Key: Answers "Why is the market moving right now?"
Produces: Narrative DNA (4th intelligence object) + Catalyst Radar

Run: python /home/z/my-project/scripts/stage10_implement.py
"""

from pathlib import Path
import textwrap

ROOT = Path("/home/z/my-project/athena-x")
ROOT.mkdir(parents=True, exist_ok=True)
FILES = []

def w(rel: str, content: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(content).lstrip("\n"))
    FILES.append(rel)


# ============================================================================
# 1. NEWS PLUGIN PROTOCOL
# ============================================================================

w("plugins/news/_base/pyproject.toml", '''
[project]
name = "athena-x-plugin-news-base"
version = "0.1.0"
description = "NewsPlugin Protocol - stable interface for news category plugins (Stage 10)"
requires-python = ">=3.11"
dependencies = ["pydantic>=2.9.0"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_plugin_news_base"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w("plugins/news/_base/src/athena_x_plugin_news_base/__init__.py", '''
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
''')

w("plugins/news/_base/src/athena_x_plugin_news_base/protocol.py", '''
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
''')

w("plugins/news/_base/tests/__init__.py", "")
w("plugins/news/_base/tests/test_protocol.py", '''
"""Tests for NewsPlugin Protocol + Narrative DNA + Catalyst Radar."""
import pytest
from datetime import datetime, timezone
from athena_x_plugin_news_base import (
    NewsPlugin, NewsEvent, NewsCategory, NewsImpact,
    EventImportance, NarrativeDNA, CatalystEvent,
)


def test_10_news_categories_defined():
    assert NewsCategory.BREAKING.value == "breaking"
    assert NewsCategory.ECONOMIC.value == "economic"
    assert NewsCategory.FED.value == "fed"
    assert NewsCategory.TREASURY.value == "treasury"
    assert NewsCategory.EARNINGS.value == "earnings"
    assert NewsCategory.GEOPOLITICAL.value == "geopolitical"
    assert NewsCategory.ENERGY.value == "energy"
    assert NewsCategory.SEMICONDUCTOR.value == "semiconductor"
    assert NewsCategory.REGULATORY.value == "regulatory"
    assert NewsCategory.ALTERNATIVE.value == "alternative"


def test_news_event_has_all_fields():
    """NewsEvent has the canonical schema fields."""
    e = NewsEvent(
        event_id="evt-1",
        timestamp=datetime.now(timezone.utc),
        source="Reuters",
        headline="CPI prints 3.2%",
        category=NewsCategory.ECONOMIC,
    )
    assert e.event_id == "evt-1"
    assert e.source == "Reuters"
    assert e.headline == "CPI prints 3.2%"
    assert e.category == NewsCategory.ECONOMIC
    assert e.importance == EventImportance.MEDIUM
    assert e.symbols == []
    assert e.sentiment is None  # not computed in Stage 10


def test_narrative_dna_has_required_fields():
    """NarrativeDNA includes primary_driver, theme, confidence, story."""
    dna = NarrativeDNA(
        primary_driver="Stronger-than-expected CPI",
        current_theme="Inflation Risk",
        confidence=0.93,
        story_of_the_day="Morning gap higher, CPI released, bond yields spike, tech sells off",
    )
    assert dna.primary_driver == "Stronger-than-expected CPI"
    assert dna.current_theme == "Inflation Risk"
    assert dna.confidence == 0.93
    assert "CPI" in dna.story_of_the_day


def test_narrative_dna_serializable():
    """NarrativeDNA can be serialized to dict."""
    dna = NarrativeDNA(primary_driver="Fed hawkish", confidence=0.85)
    d = dna.to_dict()
    assert d["primary_driver"] == "Fed hawkish"
    assert "timestamp" in d


def test_catalyst_event():
    """CatalystEvent represents an upcoming market-moving event."""
    c = CatalystEvent(
        event_id="cat-1",
        name="FOMC Rate Decision",
        scheduled_time=datetime.now(timezone.utc),
        category=NewsCategory.FED,
        importance=EventImportance.CRITICAL,
        time_horizon="this_week",
    )
    assert c.name == "FOMC Rate Decision"
    assert c.importance == EventImportance.CRITICAL
    assert c.time_horizon == "this_week"


def test_news_impact_chain():
    """NewsImpact contains directional impact chain."""
    impact = NewsImpact(
        event_id="evt-1",
        impact_chain=[
            {"asset": "Bonds", "direction": "up"},
            {"asset": "DXY", "direction": "up"},
            {"asset": "VIX", "direction": "up"},
            {"asset": "ES", "direction": "down"},
        ],
        probability=0.82,
    )
    assert len(impact.impact_chain) == 4
    assert impact.probability == 0.82


def test_protocol_is_runtime_checkable():
    class FakePlugin:
        @property
        def plugin_id(self): return "economic"
        @property
        def category(self): return NewsCategory.ECONOMIC
        @property
        def version(self): return "1.0.0"
        def classify(self, raw): return NewsEvent(
            event_id="x", timestamp=datetime.now(timezone.utc),
            source="test", headline="test", category=NewsCategory.ECONOMIC,
        )
        def assess_impact(self, event): return NewsImpact(event_id="x")

    plugin = FakePlugin()
    assert isinstance(plugin, NewsPlugin)
''')

# ============================================================================
# 2. NEWS CATEGORY MANIFESTS (10 categories)
# ============================================================================

NEWS_MANIFESTS = [
    ("breaking", "Breaking News", "breaking", 1, "Reuters, Bloomberg, CNBC, WSJ, CNN Business"),
    ("economic", "Economic Releases", "economic", 1, "CPI, PPI, NFP, GDP, Retail Sales, PMI, ISM, Housing"),
    ("fed", "Federal Reserve", "fed", 1, "FOMC, Powell, Governors, Beige Book, Minutes"),
    ("treasury", "Treasury", "treasury", 5, "Auctions, Debt Issuance, TGA"),
    ("earnings", "Earnings", "earnings", 1, "MAG7, S&P 500, Nasdaq 100, SOXX companies"),
    ("geopolitical", "Geopolitical", "geopolitical", 5, "Wars, Sanctions, Trade, Taiwan, Middle East"),
    ("energy", "Energy", "energy", 5, "OPEC, Oil, LNG, Natural Gas"),
    ("semiconductor", "Semiconductor", "semiconductor", 1, "NVDA, AMD, TSMC, AVGO, INTC, QCOM, ARM"),
    ("regulatory", "Regulatory", "regulatory", 5, "SEC, CFTC, OCC, Exchanges"),
    ("alternative", "Alternative", "alternative", 10, "Polymarket, Company announcements, Gov press releases"),
]

for slug, name, category, refresh, desc in NEWS_MANIFESTS:
    w(f"plugins/news/{slug}/manifest.yaml", f'''id: {slug}
name: "{name}"
version: "1.0.0"
category: {category}
refresh_interval_seconds: {refresh}
inputs: [raw_articles]
outputs: [classified_events, impact_assessment]
dependencies: []
enabled: true
description: "{desc}"
author: "ATHENA-X"
''')

# ============================================================================
# 3. NARRATIVE ENGINE
# ============================================================================

w("engines/narrative-engine/pyproject.toml", '''
[project]
name = "athena-x-engine-narrative-engine"
version = "0.1.0"
description = "Narrative Engine - Event Classification + Impact + Timeline + Story Generator"
requires-python = ">=3.11"
dependencies = [
    "athena-x-plugin-news-base",
    "athena-x-runtime-logger",
    "athena-x-runtime-event-envelope",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_engine_narrative_engine"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w("engines/narrative-engine/src/athena_x_engine_narrative_engine/__init__.py", '''
"""Narrative Engine."""
from .classifier import EventClassifier
from .impact import MarketImpactEngine
from .timeline import EventTimeline
from .narrative import NarrativeGenerator

__all__ = [
    "EventClassifier", "MarketImpactEngine",
    "EventTimeline", "NarrativeGenerator",
]
__version__ = "0.1.0"
''')

w("engines/narrative-engine/src/athena_x_engine_narrative_engine/classifier.py", '''
"""Event Classifier - classifies raw news into structured NewsEvent objects."""
from __future__ import annotations
import re
from typing import Any
from athena_x_plugin_news_base import NewsEvent, NewsCategory, EventImportance
from athena_x_runtime_logger import get_logger

log = get_logger("narrative.classifier")


# Keyword-based classification rules (V1 — NLP in V2)
CLASSIFICATION_RULES = {
    NewsCategory.ECONOMIC: {
        "keywords": ["CPI", "PPI", "NFP", "GDP", "retail sales", "PMI", "ISM", "housing",
                      "consumer confidence", "unemployment", "inflation", "jobless claims"],
        "importance": EventImportance.HIGH,
    },
    NewsCategory.FED: {
        "keywords": ["FOMC", "Powell", "Fed Governor", "Beige Book", "Fed Minutes",
                      "Federal Reserve", "rate cut", "rate hike", "fed funds"],
        "importance": EventImportance.CRITICAL,
    },
    NewsCategory.TREASURY: {
        "keywords": ["auction", "debt issuance", "TGA", "Treasury statement", "bond auction"],
        "importance": EventImportance.MEDIUM,
    },
    NewsCategory.EARNINGS: {
        "keywords": ["EPS", "earnings", "Q1", "Q2", "Q3", "Q4", "revenue beat", "guidance",
                      "buyback", "dividend"],
        "importance": EventImportance.HIGH,
    },
    NewsCategory.GEOPOLITICAL: {
        "keywords": ["war", "sanctions", "trade", "Taiwan", "Middle East", "China",
                      "Europe", "NATO", "Russia", "Ukraine"],
        "importance": EventImportance.HIGH,
    },
    NewsCategory.ENERGY: {
        "keywords": ["OPEC", "oil", "LNG", "natural gas", "crude", "barrel", "production cut"],
        "importance": EventImportance.MEDIUM,
    },
    NewsCategory.SEMICONDUCTOR: {
        "keywords": ["NVIDIA", "NVDA", "AMD", "TSMC", "Broadcom", "AVGO", "Intel", "INTC",
                      "Qualcomm", "QCOM", "ARM", "Samsung", "chip", "semiconductor", "wafer"],
        "importance": EventImportance.HIGH,
    },
    NewsCategory.REGULATORY: {
        "keywords": ["SEC", "CFTC", "OCC", "DOJ", "antitrust", "probe", "investigation",
                      "fine", "penalty"],
        "importance": EventImportance.MEDIUM,
    },
    NewsCategory.ALTERNATIVE: {
        "keywords": ["Polymarket", "prediction market", "press release", "announcement"],
        "importance": EventImportance.LOW,
    },
}

# Symbol extraction patterns
SYMBOL_PATTERNS = [
    (re.compile(r"\\b(NVDA|AAPL|MSFT|GOOGL|AMZN|META|TSLA)\\b"), "mag7"),
    (re.compile(r"\\b(ES|SPY|SPX|QQQ|NQ|IWM|DIA|SOXX|SMH)\\b"), "index"),
    (re.compile(r"\\b(VIX|VVIX|MOVE|TNX|DXY)\\b"), "indicator"),
    (re.compile(r"\\b(Gold|Oil|Copper|Silver)\\b"), "commodity"),
    (re.compile(r"\\b(XLK|XLF|XLV|XLY|XLI|XLE|XLP|XLB|XLU|XLRE|XLC)\\b"), "sector"),
]

# Region detection
REGION_PATTERNS = {
    "US": re.compile(r"\\b(US|United States|America|Wall Street|Fed|Treasury)\\b", re.I),
    "EU": re.compile(r"\\b(Europe|EU|Eurozone|ECB|DAX|FTSE|CAC)\\b", re.I),
    "CN": re.compile(r"\\b(China|Chinese|Beijing|Shanghai|PBoC)\\b", re.I),
    "JP": re.compile(r"\\b(Japan|Japanese|Tokyo|BoJ|Nikkei)\\b", re.I),
    "UK": re.compile(r"\\b(UK|Britain|British|BoE|FTSE)\\b", re.I),
    "Global": re.compile(r"\\b(global|worldwide|international)\\b", re.I),
}


class EventClassifier:
    """Classifies raw news articles into structured NewsEvent objects.

    Stage 10: Every news item becomes a structured event with category,
    region, symbols, importance, and confidence.
    """

    def classify(self, raw_article: dict) -> NewsEvent:
        """Classify a raw news article."""
        from uuid import uuid4
        headline = raw_article.get("headline", "")
        source = raw_article.get("source", "Unknown")
        timestamp_str = raw_article.get("published_at") or raw_article.get("timestamp", "")

        # Parse timestamp
        from datetime import datetime, timezone
        try:
            if isinstance(timestamp_str, str):
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            else:
                timestamp = datetime.now(timezone.utc)
        except Exception:
            timestamp = datetime.now(timezone.utc)

        # Classify category
        category, importance = self._classify_category(headline)

        # Extract symbols
        symbols = self._extract_symbols(headline)

        # Detect region
        region = self._detect_region(headline)

        # Detect related assets
        related_assets = self._detect_related_assets(headline, category, symbols)

        return NewsEvent(
            event_id=str(uuid4()),
            timestamp=timestamp,
            source=source,
            headline=headline,
            category=category,
            importance=importance,
            symbols=symbols,
            region=region,
            related_assets=related_assets,
            confidence=0.85,
            summary=raw_article.get("summary", ""),
            url=raw_article.get("url", ""),
        )

    def _classify_category(self, headline: str) -> tuple[NewsCategory, EventImportance]:
        """Classify the category based on headline keywords."""
        headline_lower = headline.lower()
        for category, rules in CLASSIFICATION_RULES.items():
            for keyword in rules["keywords"]:
                if keyword.lower() in headline_lower:
                    return category, rules["importance"]
        return NewsCategory.BREAKING, EventImportance.MEDIUM

    def _extract_symbols(self, headline: str) -> list[str]:
        """Extract stock symbols from headline."""
        symbols = set()
        for pattern, _ in SYMBOL_PATTERNS:
            matches = pattern.findall(headline)
            symbols.update(matches)
        return list(symbols)

    def _detect_region(self, headline: str) -> str:
        """Detect the geographic region."""
        for region, pattern in REGION_PATTERNS.items():
            if pattern.search(headline):
                return region
        return "US"  # default

    def _detect_related_assets(self, headline: str, category: NewsCategory, symbols: list[str]) -> list[str]:
        """Detect related assets based on category + symbols."""
        related = set(symbols)
        # Add related assets based on category
        if category == NewsCategory.ECONOMIC:
            related.update(["ES", "SPY", "TNX", "DXY", "VIX"])
        elif category == NewsCategory.FED:
            related.update(["ES", "SPY", "TNX", "DXY", "Gold"])
        elif category == NewsCategory.SEMICONDUCTOR:
            related.update(["SOXX", "QQQ", "NVDA"])
        elif category == NewsCategory.ENERGY:
            related.update(["Oil", "XLE"])
        elif category == NewsCategory.GEOPOLITICAL:
            related.update(["VIX", "Gold", "Oil"])
        return list(related)
''')

w("engines/narrative-engine/src/athena_x_engine_narrative_engine/impact.py", '''
"""Market Impact Engine - computes directional relationships.

Stage 10: No forecasts. Only directional relationships.

Example:
  Event: US CPI
  -> Bonds up -> DXY up -> VIX up -> ES down
  Probability: 82%
"""
from __future__ import annotations
from typing import Any
from athena_x_plugin_news_base import NewsEvent, NewsImpact, NewsCategory
from athena_x_runtime_logger import get_logger

log = get_logger("narrative.impact")


# Impact chains by category (directional, not forecasts)
IMPACT_CHAINS = {
    NewsCategory.ECONOMIC: {
        "inflation_high": [
            {"asset": "Bonds", "direction": "down"},   # yields up
            {"asset": "DXY", "direction": "up"},
            {"asset": "VIX", "direction": "up"},
            {"asset": "ES", "direction": "down"},
            {"asset": "Gold", "direction": "up"},
        ],
        "inflation_low": [
            {"asset": "Bonds", "direction": "up"},      # yields down
            {"asset": "DXY", "direction": "down"},
            {"asset": "VIX", "direction": "down"},
            {"asset": "ES", "direction": "up"},
            {"asset": "Gold", "direction": "down"},
        ],
    },
    NewsCategory.FED: {
        "hawkish": [
            {"asset": "Bonds", "direction": "down"},
            {"asset": "DXY", "direction": "up"},
            {"asset": "VIX", "direction": "up"},
            {"asset": "ES", "direction": "down"},
            {"asset": "QQQ", "direction": "down"},
        ],
        "dovish": [
            {"asset": "Bonds", "direction": "up"},
            {"asset": "DXY", "direction": "down"},
            {"asset": "VIX", "direction": "down"},
            {"asset": "ES", "direction": "up"},
            {"asset": "QQQ", "direction": "up"},
        ],
    },
    NewsCategory.GEOPOLITICAL: {
        "default": [
            {"asset": "VIX", "direction": "up"},
            {"asset": "Gold", "direction": "up"},
            {"asset": "Oil", "direction": "up"},
            {"asset": "ES", "direction": "down"},
        ],
    },
    NewsCategory.SEMICONDUCTOR: {
        "positive": [
            {"asset": "SOXX", "direction": "up"},
            {"asset": "QQQ", "direction": "up"},
            {"asset": "NVDA", "direction": "up"},
        ],
        "negative": [
            {"asset": "SOXX", "direction": "down"},
            {"asset": "QQQ", "direction": "down"},
            {"asset": "NVDA", "direction": "down"},
        ],
    },
    NewsCategory.ENERGY: {
        "supply_cut": [
            {"asset": "Oil", "direction": "up"},
            {"asset": "XLE", "direction": "up"},
            {"asset": "ES", "direction": "down"},
        ],
    },
}


class MarketImpactEngine:
    """Computes directional market impact for events.

    Stage 10 rule: No forecasts. Only directional relationships.
    """

    def assess_impact(self, event: NewsEvent) -> NewsImpact:
        """Assess the market impact of an event."""
        chain = self._get_impact_chain(event)
        probability = self._estimate_probability(event, chain)
        confidence = self._estimate_confidence(event)

        return NewsImpact(
            event_id=event.event_id,
            impact_chain=chain,
            probability=probability,
            confidence=confidence,
        )

    def _get_impact_chain(self, event: NewsEvent) -> list[dict]:
        """Get the directional impact chain for an event."""
        category_chains = IMPACT_CHAINS.get(event.category, {})

        # Determine sub-type from headline
        headline_lower = event.headline.lower()
        if event.category == NewsCategory.ECONOMIC:
            if any(w in headline_lower for w in ["higher", "hot", "above", "beat"]):
                return category_chains.get("inflation_high", [])
            elif any(w in headline_lower for w in ["lower", "cool", "below", "miss"]):
                return category_chains.get("inflation_low", [])
        elif event.category == NewsCategory.FED:
            if any(w in headline_lower for w in ["hawkish", "higher", "hike", "hold"]):
                return category_chains.get("hawkish", [])
            elif any(w in headline_lower for w in ["dovish", "cut", "lower", "pause"]):
                return category_chains.get("dovish", [])
        elif event.category == NewsCategory.SEMICONDUCTOR:
            if any(w in headline_lower for w in ["beat", "strong", "upgrade", "surge"]):
                return category_chains.get("positive", [])
            elif any(w in headline_lower for w in ["miss", "weak", "downgrade", "fall"]):
                return category_chains.get("negative", [])

        return category_chains.get("default", [])

    def _estimate_probability(self, event: NewsEvent, chain: list[dict]) -> float:
        """Estimate the probability of the impact chain occurring."""
        if not chain:
            return 0.3
        # Higher importance = higher probability
        prob_map = {"critical": 0.85, "high": 0.75, "medium": 0.60, "low": 0.40}
        return prob_map.get(event.importance.value, 0.50)

    def _estimate_confidence(self, event: NewsEvent) -> float:
        """Estimate confidence in the impact assessment."""
        # More symbols = more context = higher confidence
        base = 0.6
        if len(event.symbols) > 0:
            base += 0.1
        if len(event.related_assets) > 2:
            base += 0.1
        if event.importance.value in ("critical", "high"):
            base += 0.1
        return min(1.0, base)
''')

w("engines/narrative-engine/src/athena_x_engine_narrative_engine/timeline.py", '''
"""Event Timeline - maintains a live timeline of all events."""
from __future__ import annotations
from collections import deque
from datetime import datetime, timezone
from threading import RLock
from typing import Any
from athena_x_plugin_news_base import NewsEvent


class EventTimeline:
    """Maintains a live timeline of market events.

    Stage 10: Allows later stages to anticipate volatility windows.
    """

    def __init__(self, max_events: int = 1000):
        self._events: deque = deque(maxlen=max_events)
        self._lock = RLock()

    def add_event(self, event: NewsEvent) -> None:
        """Add an event to the timeline."""
        with self._lock:
            self._events.append({
                "event_id": event.event_id,
                "timestamp": event.timestamp.isoformat(),
                "time": event.timestamp.strftime("%H:%M"),
                "source": event.source,
                "headline": event.headline,
                "category": event.category.value,
                "importance": event.importance.value,
                "symbols": event.symbols,
            })

    def get_timeline(self, limit: int = 50) -> list[dict]:
        """Get the recent timeline."""
        with self._lock:
            return list(self._events)[-limit:]

    def get_events_by_category(self, category: str) -> list[dict]:
        """Filter timeline by category."""
        with self._lock:
            return [e for e in self._events if e["category"] == category]

    def get_critical_events(self) -> list[dict]:
        """Get only critical/high importance events."""
        with self._lock:
            return [e for e in self._events if e["importance"] in ("critical", "high")]

    def count(self) -> int:
        with self._lock:
            return len(self._events)
''')

# Fix path typo
import os
bad = ROOT / "engines/narrative-engine/src/athena_x_engine_narrative_engine/timeline.py',"
if bad.exists():
    os.rename(bad, ROOT / "engines/narrative-engine/src/athena_x_engine_narrative_engine/timeline.py")

w("engines/narrative-engine/src/athena_x_engine_narrative_engine/narrative.py", '''
"""Narrative Generator - produces a coherent market narrative.

Stage 10: Rather than 200 news articles, produce one coherent market narrative.

Example:
  Primary Driver: Stronger-than-expected CPI
  Secondary Driver: Higher Treasury yields
  Supporting Evidence: DXY strengthening, VIX rising, QQQ underperforming
  Current Theme: Inflation Risk
  Confidence: 93%
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
from athena_x_plugin_news_base import NewsEvent, NewsImpact, NarrativeDNA, NewsCategory
from athena_x_runtime_logger import get_logger

log = get_logger("narrative.generator")


class NarrativeGenerator:
    """Generates a coherent market narrative from events + impacts.

    Usage:
        gen = NarrativeGenerator()
        gen.add_event(event, impact)
        dna = gen.generate_narrative()
    """

    def __init__(self):
        self._events: list[tuple[NewsEvent, NewsImpact]] = []
        self._story_parts: list[str] = []

    def add_event(self, event: NewsEvent, impact: NewsImpact) -> None:
        """Add an event + its impact to the narrative."""
        self._events.append((event, impact))

    def generate_narrative(self) -> NarrativeDNA:
        """Generate the market narrative DNA."""
        if not self._events:
            return NarrativeDNA(
                primary_driver="No significant events",
                current_theme="Quiet",
                confidence=0.5,
            )

        # Find the primary driver (highest importance + highest probability impact)
        sorted_events = sorted(
            self._events,
            key=lambda x: (
                x[0].importance.value == "critical",
                x[0].importance.value == "high",
                x[1].probability,
            ),
            reverse=True,
        )

        primary_event, primary_impact = sorted_events[0]
        primary_driver = primary_event.headline

        # Secondary driver
        secondary_driver = None
        if len(sorted_events) > 1:
            secondary_driver = sorted_events[1][0].headline

        # Determine theme
        theme = self._determine_theme(primary_event)

        # Supporting evidence
        evidence = self._gather_evidence(sorted_events)

        # Impact summary
        impact_summary = self._build_impact_summary(sorted_events)

        # Story of the day
        story = self._generate_story(sorted_events)

        # Event timeline
        timeline = [
            {
                "time": e[0].timestamp.strftime("%H:%M"),
                "headline": e[0].headline,
                "category": e[0].category.value,
                "importance": e[0].importance.value,
            }
            for e in sorted_events
        ]

        # Active events
        active_events = [
            {
                "event_id": e[0].event_id,
                "headline": e[0].headline,
                "category": e[0].category.value,
                "importance": e[0].importance.value,
                "impact": e[1].impact_chain[:3],
            }
            for e in sorted_events[:5]
        ]

        # Confidence
        confidence = self._compute_confidence(sorted_events)

        return NarrativeDNA(
            primary_driver=primary_driver,
            secondary_driver=secondary_driver,
            current_theme=theme,
            confidence=confidence,
            supporting_evidence=evidence,
            event_timeline=timeline,
            impact_summary=impact_summary,
            story_of_the_day=story,
            active_events=active_events,
        )

    def _determine_theme(self, event: NewsEvent) -> str:
        """Determine the market theme from the primary event."""
        theme_map = {
            NewsCategory.ECONOMIC: "Inflation Risk" if "high" in event.headline.lower() else "Growth",
            NewsCategory.FED: "Monetary Policy",
            NewsCategory.GEOPOLITICAL: "Geopolitical Risk",
            NewsCategory.ENERGY: "Energy Supply",
            NewsCategory.SEMICONDUCTOR: "Tech Sector",
            NewsCategory.EARNINGS: "Corporate Earnings",
            NewsCategory.TREASURY: "Liquidity",
            NewsCategory.REGULATORY: "Regulatory Risk",
            NewsCategory.BREAKING: "Market Moving",
            NewsCategory.ALTERNATIVE: "Alternative Signals",
        }
        return theme_map.get(event.category, "Unknown")

    def _gather_evidence(self, events: list[tuple[NewsEvent, NewsImpact]]) -> list[str]:
        """Gather supporting evidence from impacts."""
        evidence = set()
        for event, impact in events[:5]:
            for item in impact.impact_chain:
                evidence.add(f"{item['asset']} {item['direction']}")
        return list(evidence)[:10]

    def _build_impact_summary(self, events: list[tuple[NewsEvent, NewsImpact]]) -> dict[str, str]:
        """Build a summary of directional impacts."""
        summary: dict[str, str] = {}
        for _, impact in events:
            for item in impact.impact_chain:
                asset = item["asset"]
                direction = item["direction"]
                if asset not in summary:
                    summary[asset] = direction
        return summary

    def _generate_story(self, events: list[tuple[NewsEvent, NewsImpact]]) -> str:
        """Generate a story of the day."""
        if not events:
            return "Quiet session with no major catalysts."

        parts = []
        for event, impact in events[:5]:
            time_str = event.timestamp.strftime("%H:%M")
            parts.append(f"{time_str}: {event.headline}")

        return " -> ".join(parts)

    def _compute_confidence(self, events: list[tuple[NewsEvent, NewsImpact]]) -> float:
        """Compute overall narrative confidence."""
        if not events:
            return 0.5
        # More events = higher confidence
        base = 0.60
        if len(events) >= 3:
            base += 0.10
        if len(events) >= 5:
            base += 0.10
        # Critical events boost confidence
        if any(e[0].importance.value == "critical" for e in events):
            base += 0.10
        return min(1.0, base)
''')

w("engines/narrative-engine/tests/__init__.py", "")
w("engines/narrative-engine/tests/test_engine.py", '''
"""Tests for Narrative Engine."""
import pytest
from datetime import datetime, timezone
from athena_x_plugin_news_base import NewsEvent, NewsCategory, EventImportance
from athena_x_engine_narrative_engine import (
    EventClassifier, MarketImpactEngine,
    EventTimeline, NarrativeGenerator,
)


# ============================================================================
# Event Classifier tests
# ============================================================================

def test_classifier_classifies_economic():
    """Classifier detects economic news."""
    classifier = EventClassifier()
    event = classifier.classify({
        "headline": "CPI prints 3.2% vs 3.4% expected",
        "source": "Reuters",
        "published_at": datetime.now(timezone.utc).isoformat(),
    })
    assert event.category == NewsCategory.ECONOMIC
    assert event.importance == EventImportance.HIGH


def test_classifier_classifies_fed():
    """Classifier detects Fed news."""
    classifier = EventClassifier()
    event = classifier.classify({
        "headline": "Powell signals rate cut at next FOMC meeting",
        "source": "Bloomberg",
    })
    assert event.category == NewsCategory.FED
    assert event.importance == EventImportance.CRITICAL


def test_classifier_classifies_semiconductor():
    """Classifier detects semiconductor news."""
    classifier = EventClassifier()
    event = classifier.classify({
        "headline": "NVDA beats Q3 EPS estimates by 4%",
        "source": "CNBC",
    })
    assert event.category == NewsCategory.SEMICONDUCTOR
    assert "NVDA" in event.symbols


def test_classifier_extracts_symbols():
    """Classifier extracts stock symbols."""
    classifier = EventClassifier()
    event = classifier.classify({
        "headline": "AAPL and MSFT announce partnership",
        "source": "WSJ",
    })
    assert "AAPL" in event.symbols
    assert "MSFT" in event.symbols


def test_classifier_detects_region():
    """Classifier detects geographic region."""
    classifier = EventClassifier()
    event = classifier.classify({
        "headline": "China announces new trade restrictions",
        "source": "Reuters",
    })
    assert event.region == "CN"


def test_classifier_detects_related_assets():
    """Classifier detects related assets."""
    classifier = EventClassifier()
    event = classifier.classify({
        "headline": "CPI prints higher than expected",
        "source": "Reuters",
    })
    assert "ES" in event.related_assets
    assert "VIX" in event.related_assets


# ============================================================================
# Market Impact Engine tests
# ============================================================================

def test_impact_engine_assesses_cpi():
    """Impact engine produces directional chain for CPI."""
    engine = MarketImpactEngine()
    event = NewsEvent(
        event_id="e1", timestamp=datetime.now(timezone.utc),
        source="Reuters", headline="CPI prints higher than expected",
        category=NewsCategory.ECONOMIC, importance=EventImportance.HIGH,
    )
    impact = engine.assess_impact(event)
    assert len(impact.impact_chain) > 0
    assert impact.probability > 0.5


def test_impact_engine_fed_hawkish():
    """Impact engine detects hawkish Fed."""
    engine = MarketImpactEngine()
    event = NewsEvent(
        event_id="e2", timestamp=datetime.now(timezone.utc),
        source="Bloomberg", headline="Powell signals rate hike",
        category=NewsCategory.FED, importance=EventImportance.CRITICAL,
    )
    impact = engine.assess_impact(event)
    # Should have directional impacts
    assets = [item["asset"] for item in impact.impact_chain]
    assert "ES" in assets or "Bonds" in assets


def test_impact_engine_no_forecasts():
    """Stage 10 rule: Impact engine produces directional relationships, not forecasts."""
    engine = MarketImpactEngine()
    event = NewsEvent(
        event_id="e3", timestamp=datetime.now(timezone.utc),
        source="Test", headline="Test event",
        category=NewsCategory.BREAKING,
    )
    impact = engine.assess_impact(event)
    # Impact chain has directions (up/down), not price targets
    for item in impact.impact_chain:
        assert item["direction"] in ("up", "down")


# ============================================================================
# Event Timeline tests
# ============================================================================

def test_timeline_adds_events():
    """Timeline maintains events in order."""
    timeline = EventTimeline()
    for i in range(5):
        timeline.add_event(NewsEvent(
            event_id=f"e{i}", timestamp=datetime.now(timezone.utc),
            source="test", headline=f"Event {i}",
            category=NewsCategory.BREAKING,
        ))
    assert timeline.count() == 5


def test_timeline_filters_by_category():
    """Timeline can filter by category."""
    timeline = EventTimeline()
    timeline.add_event(NewsEvent(
        event_id="e1", timestamp=datetime.now(timezone.utc),
        source="test", headline="CPI",
        category=NewsCategory.ECONOMIC,
    ))
    timeline.add_event(NewsEvent(
        event_id="e2", timestamp=datetime.now(timezone.utc),
        source="test", headline="NVDA",
        category=NewsCategory.SEMICONDUCTOR,
    ))
    economic = timeline.get_events_by_category("economic")
    assert len(economic) == 1


def test_timeline_critical_events():
    """Timeline can filter critical events."""
    timeline = EventTimeline()
    timeline.add_event(NewsEvent(
        event_id="e1", timestamp=datetime.now(timezone.utc),
        source="test", headline="Fed emergency",
        category=NewsCategory.FED, importance=EventImportance.CRITICAL,
    ))
    timeline.add_event(NewsEvent(
        event_id="e2", timestamp=datetime.now(timezone.utc),
        source="test", headline="Minor news",
        category=NewsCategory.BREAKING, importance=EventImportance.LOW,
    ))
    critical = timeline.get_critical_events()
    assert len(critical) == 1


# ============================================================================
# Narrative Generator tests
# ============================================================================

def test_narrative_generator_produces_dna():
    """Narrative generator produces NarrativeDNA."""
    gen = NarrativeGenerator()
    event = NewsEvent(
        event_id="e1", timestamp=datetime.now(timezone.utc),
        source="Reuters", headline="CPI prints higher than expected",
        category=NewsCategory.ECONOMIC, importance=EventImportance.HIGH,
    )
    impact = MarketImpactEngine().assess_impact(event)
    gen.add_event(event, impact)

    dna = gen.generate_narrative()
    assert dna.primary_driver is not None
    assert "CPI" in dna.primary_driver
    assert dna.current_theme is not None
    assert dna.confidence > 0


def test_narrative_includes_story():
    """Narrative includes a story of the day."""
    gen = NarrativeGenerator()
    for i in range(3):
        event = NewsEvent(
            event_id=f"e{i}", timestamp=datetime.now(timezone.utc),
            source="test", headline=f"Event {i}",
            category=NewsCategory.ECONOMIC,
        )
        impact = MarketImpactEngine().assess_impact(event)
        gen.add_event(event, impact)

    dna = gen.generate_narrative()
    assert len(dna.story_of_the_day) > 0


def test_narrative_includes_impact_summary():
    """Narrative includes directional impact summary."""
    gen = NarrativeGenerator()
    event = NewsEvent(
        event_id="e1", timestamp=datetime.now(timezone.utc),
        source="Reuters", headline="CPI higher",
        category=NewsCategory.ECONOMIC, importance=EventImportance.HIGH,
    )
    impact = MarketImpactEngine().assess_impact(event)
    gen.add_event(event, impact)

    dna = gen.generate_narrative()
    assert len(dna.impact_summary) > 0
    # Should have directional impacts
    for asset, direction in dna.impact_summary.items():
        assert direction in ("up", "down")


def test_narrative_includes_timeline():
    """Narrative includes event timeline."""
    gen = NarrativeGenerator()
    for i in range(3):
        event = NewsEvent(
            event_id=f"e{i}", timestamp=datetime.now(timezone.utc),
            source="test", headline=f"Event {i}",
            category=NewsCategory.ECONOMIC,
        )
        impact = MarketImpactEngine().assess_impact(event)
        gen.add_event(event, impact)

    dna = gen.generate_narrative()
    assert len(dna.event_timeline) == 3
''')

# ============================================================================
# 4. NARRATIVE INTELLIGENCE AGENT + CATALYST RADAR
# ============================================================================

w("agents/narrative-intelligence/pyproject.toml", '''
[project]
name = "athena-x-agent-narrative-intelligence"
version = "0.1.0"
description = "Narrative DNA Agent + Catalyst Radar Agent (Stage 10)"
requires-python = ">=3.11"
dependencies = [
    "athena-x-engine-narrative-engine",
    "athena-x-runtime-event-envelope",
    "athena-x-runtime-logger",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_agent_narrative_intelligence"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w("agents/narrative-intelligence/src/athena_x_agent_narrative_intelligence/__init__.py", '''
"""Narrative DNA Agent + Catalyst Radar Agent."""
from .narrative_agent import NarrativeDNAAgent
from .catalyst_radar import CatalystRadarAgent

__all__ = ["NarrativeDNAAgent", "CatalystRadarAgent"]
__version__ = "0.1.0"
''')

w("agents/narrative-intelligence/src/athena_x_agent_narrative_intelligence/narrative_agent.py", '''
"""Narrative DNA Agent - produces the 4th intelligence object.

Stage 10: Continuously publishes NarrativeDNA for downstream AI consumption.
Stages 11+ (Forecast, Probability, Reports, Supervisor) consume this object.

Usage:
    agent = NarrativeDNAAgent(event_bus=bus)
    agent.add_raw_article({"headline": "CPI prints 3.2%", "source": "Reuters"})
    dna = await agent.compute_narrative()
"""
from __future__ import annotations
from typing import Any
from athena_x_runtime_logger import get_logger
from athena_x_runtime_event_envelope import create_event, EventPriority
from athena_x_engine_narrative_engine import (
    EventClassifier, MarketImpactEngine, NarrativeGenerator,
)
from athena_x_plugin_news_base import NarrativeDNA

log = get_logger("narrative-intelligence.dna")


class NarrativeDNAAgent:
    """Produces NarrativeDNA from raw news articles.

    Pipeline:
      1. Classify raw articles into NewsEvents
      2. Assess market impact for each event
      3. Generate coherent narrative via NarrativeGenerator
      4. Publish NarrativeDNA as ai:news:narrative_dna event
    """

    def __init__(self, event_bus: Any = None):
        self._bus = event_bus
        self._classifier = EventClassifier()
        self._impact_engine = MarketImpactEngine()
        self._generator = NarrativeGenerator()
        self._dna_count = 0

    def add_raw_article(self, article: dict) -> None:
        """Add a raw news article for processing."""
        event = self._classifier.classify(article)
        impact = self._impact_engine.assess_impact(event)
        self._generator.add_event(event, impact)

    async def compute_narrative(self) -> NarrativeDNA:
        """Compute and publish the NarrativeDNA."""
        dna = self._generator.generate_narrative()
        self._dna_count += 1

        if self._bus is not None:
            event = create_event(
                event_type="ai:news:narrative_dna",
                source_agent="narrative-intelligence.dna",
                symbol="*",
                priority=EventPriority.HIGH,
                payload=dna.to_dict(),
            )
            await self._bus.publish(event)

        return dna

    def get_stats(self) -> dict:
        return {"narratives_computed": self._dna_count}
''')

w("agents/narrative-intelligence/src/athena_x_agent_narrative_intelligence/catalyst_radar.py", '''
"""Catalyst Radar Agent - tracks upcoming market-moving events.

Stage 10: Gives every downstream AI agent awareness of upcoming risks.

Time horizons:
  - Next 15 minutes
  - Next hour
  - Today
  - This week (CPI, FOMC, NFP, OPEX, Treasury auctions, earnings)
"""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from typing import Any
from dataclasses import dataclass, field
from athena_x_runtime_logger import get_logger
from athena_x_runtime_event_envelope import create_event, EventPriority
from athena_x_plugin_news_base import CatalystEvent, NewsCategory, EventImportance

log = get_logger("narrative-intelligence.catalyst_radar")


class CatalystRadarAgent:
    """Tracks upcoming market-moving events.

    Usage:
        radar = CatalystRadarAgent(event_bus=bus)
        radar.add_catalyst(CatalystEvent(
            event_id="c1", name="CPI Release",
            scheduled_time=datetime.now(timezone.utc) + timedelta(hours=2),
            category=NewsCategory.ECONOMIC,
            importance=EventImportance.CRITICAL,
        ))
        upcoming = radar.get_upcoming(time_horizon="today")
    """

    def __init__(self, event_bus: Any = None):
        self._bus = event_bus
        self._catalysts: list[CatalystEvent] = []
        self._publish_count = 0

    def add_catalyst(self, catalyst: CatalystEvent) -> None:
        """Add an upcoming catalyst to the radar."""
        self._catalysts.append(catalyst)
        log.info("catalyst_added",
                 name=catalyst.name,
                 scheduled=catalyst.scheduled_time.isoformat(),
                 importance=catalyst.importance.value)

    def remove_catalyst(self, event_id: str) -> None:
        """Remove a catalyst."""
        self._catalysts = [c for c in self._catalysts if c.event_id != event_id]

    def get_upcoming(self, time_horizon: str = "today") -> list[CatalystEvent]:
        """Get upcoming catalysts within a time horizon."""
        now = datetime.now(timezone.utc)
        horizon_map = {
            "15min": timedelta(minutes=15),
            "1hour": timedelta(hours=1),
            "today": timedelta(hours=24),
            "this_week": timedelta(days=7),
        }
        delta = horizon_map.get(time_horizon, timedelta(hours=24))
        deadline = now + delta

        upcoming = [
            c for c in self._catalysts
            if now <= c.scheduled_time <= deadline
        ]
        # Sort by scheduled time
        upcoming.sort(key=lambda c: c.scheduled_time)
        return upcoming

    def get_next_catalyst(self) -> CatalystEvent | None:
        """Get the very next catalyst."""
        now = datetime.now(timezone.utc)
        future = [c for c in self._catalysts if c.scheduled_time > now]
        if not future:
            return None
        return min(future, key=lambda c: c.scheduled_time)

    def get_critical_upcoming(self) -> list[CatalystEvent]:
        """Get only critical/high importance upcoming catalysts."""
        return [
            c for c in self.get_upcoming("this_week")
            if c.importance in (EventImportance.CRITICAL, EventImportance.HIGH)
        ]

    async def publish_radar(self) -> dict:
        """Publish the catalyst radar as an event."""
        self._publish_count += 1

        payload = {
            "published_at": datetime.now(timezone.utc).isoformat(),
            "next_15min": [self._catalyst_to_dict(c) for c in self.get_upcoming("15min")],
            "next_1hour": [self._catalyst_to_dict(c) for c in self.get_upcoming("1hour")],
            "today": [self._catalyst_to_dict(c) for c in self.get_upcoming("today")],
            "this_week": [self._catalyst_to_dict(c) for c in self.get_upcoming("this_week")],
            "next_catalyst": self._catalyst_to_dict(self.get_next_catalyst()) if self.get_next_catalyst() else None,
            "critical_upcoming_count": len(self.get_critical_upcoming()),
        }

        if self._bus is not None:
            event = create_event(
                event_type="ai:news:catalyst_radar",
                source_agent="narrative-intelligence.catalyst_radar",
                symbol="*",
                priority=EventPriority.HIGH,
                payload=payload,
            )
            await self._bus.publish(event)

        return payload

    def _catalyst_to_dict(self, c: CatalystEvent) -> dict:
        return {
            "event_id": c.event_id,
            "name": c.name,
            "scheduled_time": c.scheduled_time.isoformat(),
            "category": c.category.value,
            "importance": c.importance.value,
            "symbols": c.symbols,
            "time_horizon": c.time_horizon,
            "description": c.description,
        }

    def get_stats(self) -> dict:
        return {
            "total_catalysts": len(self._catalysts),
            "publish_count": self._publish_count,
        }
''')

w("agents/narrative-intelligence/tests/__init__.py", "")
w("agents/narrative-intelligence/tests/test_agents.py", '''
"""Tests for Narrative DNA Agent + Catalyst Radar Agent."""
import pytest
from datetime import datetime, timezone, timedelta
from athena_x_agent_narrative_intelligence import NarrativeDNAAgent, CatalystRadarAgent
from athena_x_plugin_news_base import CatalystEvent, NewsCategory, EventImportance


# ============================================================================
# Narrative DNA Agent tests
# ============================================================================

async def test_narrative_dna_produced():
    """Narrative DNA Agent produces DNA from raw articles."""
    agent = NarrativeDNAAgent()
    agent.add_raw_article({
        "headline": "CPI prints 3.2% vs 3.4% expected",
        "source": "Reuters",
        "published_at": datetime.now(timezone.utc).isoformat(),
    })
    agent.add_raw_article({
        "headline": "Fed Governor signals patience on rate cuts",
        "source": "Bloomberg",
    })
    dna = await agent.compute_narrative()
    assert dna.primary_driver is not None
    assert dna.current_theme is not None
    assert dna.confidence > 0


async def test_narrative_dna_event_published():
    """Narrative DNA publishes ai:news:narrative_dna event."""
    from athena_x_runtime_event_bus import InMemoryBusClient

    bus = InMemoryBusClient()
    agent = NarrativeDNAAgent(event_bus=bus)

    received = []
    async def handler(event):
        received.append(event)
    await bus.subscribe("ai:news:narrative_dna", handler)

    agent.add_raw_article({"headline": "CPI higher", "source": "Reuters"})
    await agent.compute_narrative()

    assert len(received) == 1
    assert "primary_driver" in received[0].payload
    await bus.close()


async def test_narrative_includes_story():
    """Narrative DNA includes story of the day."""
    agent = NarrativeDNAAgent()
    agent.add_raw_article({"headline": "Morning gap higher", "source": "CNBC"})
    agent.add_raw_article({"headline": "CPI released hot", "source": "Reuters"})
    agent.add_raw_article({"headline": "Tech sells off", "source": "WSJ"})
    dna = await agent.compute_narrative()
    assert len(dna.story_of_the_day) > 0


async def test_narrative_includes_impact_summary():
    """Narrative DNA includes directional impact summary."""
    agent = NarrativeDNAAgent()
    agent.add_raw_article({"headline": "CPI higher than expected", "source": "Reuters"})
    dna = await agent.compute_narrative()
    assert len(dna.impact_summary) > 0


async def test_narrative_includes_timeline():
    """Narrative DNA includes event timeline."""
    agent = NarrativeDNAAgent()
    for i in range(3):
        agent.add_raw_article({
            "headline": f"Event {i}",
            "source": "test",
            "published_at": datetime.now(timezone.utc).isoformat(),
        })
    dna = await agent.compute_narrative()
    assert len(dna.event_timeline) == 3


# ============================================================================
# Catalyst Radar Agent tests
# ============================================================================

def test_radar_adds_catalyst():
    """Radar can add upcoming catalysts."""
    radar = CatalystRadarAgent()
    radar.add_catalyst(CatalystEvent(
        event_id="c1", name="CPI Release",
        scheduled_time=datetime.now(timezone.utc) + timedelta(hours=2),
        category=NewsCategory.ECONOMIC,
        importance=EventImportance.CRITICAL,
    ))
    assert len(radar.get_upcoming("this_week")) == 1


def test_radar_filters_by_horizon():
    """Radar filters by time horizon."""
    radar = CatalystRadarAgent()
    # Near-term catalyst
    radar.add_catalyst(CatalystEvent(
        event_id="c1", name="Fed Speaker",
        scheduled_time=datetime.now(timezone.utc) + timedelta(minutes=10),
        category=NewsCategory.FED,
        importance=EventImportance.HIGH,
        time_horizon="15min",
    ))
    # Far catalyst
    radar.add_catalyst(CatalystEvent(
        event_id="c2", name="FOMC",
        scheduled_time=datetime.now(timezone.utc) + timedelta(days=3),
        category=NewsCategory.FED,
        importance=EventImportance.CRITICAL,
        time_horizon="this_week",
    ))

    near = radar.get_upcoming("15min")
    assert len(near) == 1
    assert near[0].name == "Fed Speaker"

    far = radar.get_upcoming("this_week")
    assert len(far) == 2


def test_radar_gets_next_catalyst():
    """Radar finds the very next catalyst."""
    radar = CatalystRadarAgent()
    radar.add_catalyst(CatalystEvent(
        event_id="c1", name="FOMC",
        scheduled_time=datetime.now(timezone.utc) + timedelta(days=3),
        category=NewsCategory.FED,
        importance=EventImportance.CRITICAL,
    ))
    radar.add_catalyst(CatalystEvent(
        event_id="c2", name="CPI",
        scheduled_time=datetime.now(timezone.utc) + timedelta(hours=2),
        category=NewsCategory.ECONOMIC,
        importance=EventImportance.CRITICAL,
    ))

    next_cat = radar.get_next_catalyst()
    assert next_cat is not None
    assert next_cat.name == "CPI"  # sooner


def test_radar_critical_upcoming():
    """Radar identifies critical upcoming catalysts."""
    radar = CatalystRadarAgent()
    radar.add_catalyst(CatalystEvent(
        event_id="c1", name="FOMC",
        scheduled_time=datetime.now(timezone.utc) + timedelta(days=1),
        category=NewsCategory.FED,
        importance=EventImportance.CRITICAL,
    ))
    radar.add_catalyst(CatalystEvent(
        event_id="c2", name="Minor Report",
        scheduled_time=datetime.now(timezone.utc) + timedelta(hours=2),
        category=NewsCategory.ECONOMIC,
        importance=EventImportance.LOW,
    ))

    critical = radar.get_critical_upcoming()
    assert len(critical) == 1
    assert critical[0].name == "FOMC"


async def test_radar_publishes_event():
    """Radar publishes ai:news:catalyst_radar event."""
    from athena_x_runtime_event_bus import InMemoryBusClient

    bus = InMemoryBusClient()
    radar = CatalystRadarAgent(event_bus=bus)

    received = []
    async def handler(event):
        received.append(event)
    await bus.subscribe("ai:news:catalyst_radar", handler)

    radar.add_catalyst(CatalystEvent(
        event_id="c1", name="CPI",
        scheduled_time=datetime.now(timezone.utc) + timedelta(hours=2),
        category=NewsCategory.ECONOMIC,
        importance=EventImportance.CRITICAL,
    ))
    await radar.publish_radar()

    assert len(received) == 1
    assert "next_15min" in received[0].payload
    assert "today" in received[0].payload
    assert "this_week" in received[0].payload
    await bus.close()
''')

# ============================================================================
# 5. STAGE 10 INTEGRATION
# ============================================================================

w("runtime/stage10-integration/pyproject.toml", '''
[project]
name = "athena-x-runtime-stage10-integration"
version = "0.1.0"
description = "Stage 10 integration - Market Narrative Intelligence Platform tests"
requires-python = ">=3.11"
dependencies = [
    "athena-x-engine-narrative-engine",
    "athena-x-agent-narrative-intelligence",
    "athena-x-runtime-event-bus",
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_runtime_stage10_integration"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w("runtime/stage10-integration/src/athena_x_runtime_stage10_integration/__init__.py", '''"""Stage 10 integration."""''')

w("runtime/stage10-integration/tests/__init__.py", "")
w("runtime/stage10-integration/tests/test_stage10_acceptance.py", '''
"""Stage 10 acceptance tests - Market Narrative Intelligence Platform."""
import pytest
from datetime import datetime, timezone, timedelta
from athena_x_plugin_news_base import NewsCategory, EventImportance, CatalystEvent
from athena_x_engine_narrative_engine import (
    EventClassifier, MarketImpactEngine, EventTimeline, NarrativeGenerator,
)
from athena_x_agent_narrative_intelligence import NarrativeDNAAgent, CatalystRadarAgent


# ============================================================================
# Exit Criteria 1: News classification works
# ============================================================================

def test_classifies_all_10_categories():
    """All 10 news categories can be classified."""
    classifier = EventClassifier()
    test_cases = [
        ("Breaking news update", NewsCategory.BREAKING),
        ("CPI prints 3.2%", NewsCategory.ECONOMIC),
        ("Powell signals rate cut", NewsCategory.FED),
        ("Treasury auction results", NewsCategory.TREASURY),
        ("NVDA beats earnings", NewsCategory.EARNINGS),
        ("China trade restrictions", NewsCategory.GEOPOLITICAL),
        ("OPEC production cut", NewsCategory.ENERGY),
        ("TSMC reports strong demand", NewsCategory.SEMICONDUCTOR),
        ("SEC opens probe", NewsCategory.REGULATORY),
        ("Polymarket prediction", NewsCategory.ALTERNATIVE),
    ]
    for headline, expected_cat in test_cases:
        event = classifier.classify({"headline": headline, "source": "test"})
        assert event.category == expected_cat, f"Expected {expected_cat}, got {event.category} for '{headline}'"


# ============================================================================
# Exit Criteria 2: Market Impact Engine produces directional relationships
# ============================================================================

def test_impact_engine_produces_directional_chain():
    """Impact engine produces directional chain (not forecasts)."""
    engine = MarketImpactEngine()
    classifier = EventClassifier()
    event = classifier.classify({"headline": "CPI higher than expected", "source": "Reuters"})
    impact = engine.assess_impact(event)
    assert len(impact.impact_chain) > 0
    # All directions are directional (up/down), not price targets
    for item in impact.impact_chain:
        assert item["direction"] in ("up", "down")


# ============================================================================
# Exit Criteria 3: Event Timeline maintained
# ============================================================================

def test_timeline_maintains_events():
    """Timeline maintains all events for the day."""
    timeline = EventTimeline()
    for i in range(10):
        classifier = EventClassifier()
        event = classifier.classify({"headline": f"Event {i}", "source": "test"})
        timeline.add_event(event)
    assert timeline.count() == 10


# ============================================================================
# Exit Criteria 4: Narrative DNA produced
# ============================================================================

async def test_narrative_dna_produced():
    """Narrative DNA Agent produces a coherent narrative."""
    agent = NarrativeDNAAgent()
    agent.add_raw_article({"headline": "CPI prints higher", "source": "Reuters"})
    agent.add_raw_article({"headline": "Bond yields spike", "source": "Bloomberg"})
    agent.add_raw_article({"headline": "Tech sells off", "source": "CNBC"})

    dna = await agent.compute_narrative()
    assert dna.primary_driver is not None
    assert dna.current_theme is not None
    assert dna.confidence > 0
    assert len(dna.story_of_the_day) > 0
    assert len(dna.event_timeline) == 3


# ============================================================================
# Exit Criteria 5: Catalyst Radar tracks upcoming events
# ============================================================================

def test_catalyst_radar_tracks_upcoming():
    """Catalyst Radar tracks events across time horizons."""
    radar = CatalystRadarAgent()
    radar.add_catalyst(CatalystEvent(
        event_id="c1", name="CPI",
        scheduled_time=datetime.now(timezone.utc) + timedelta(hours=2),
        category=NewsCategory.ECONOMIC,
        importance=EventImportance.CRITICAL,
    ))
    radar.add_catalyst(CatalystEvent(
        event_id="c2", name="FOMC",
        scheduled_time=datetime.now(timezone.utc) + timedelta(days=3),
        category=NewsCategory.FED,
        importance=EventImportance.CRITICAL,
    ))

    today = radar.get_upcoming("today")
    this_week = radar.get_upcoming("this_week")
    assert len(today) == 1  # CPI is today
    assert len(this_week) == 2  # CPI + FOMC


# ============================================================================
# Exit Criteria 6: Events emitted as ai:news:* and ai:macro:*
# ============================================================================

async def test_narrative_dna_event_published():
    """Narrative DNA publishes ai:news:narrative_dna event."""
    from athena_x_runtime_event_bus import InMemoryBusClient

    bus = InMemoryBusClient()
    agent = NarrativeDNAAgent(event_bus=bus)

    received = []
    async def handler(event):
        received.append(event)
    await bus.subscribe("ai:news:narrative_dna", handler)

    agent.add_raw_article({"headline": "Fed cuts rates", "source": "Reuters"})
    await agent.compute_narrative()

    assert len(received) == 1
    await bus.close()


async def test_catalyst_radar_event_published():
    """Catalyst Radar publishes ai:news:catalyst_radar event."""
    from athena_x_runtime_event_bus import InMemoryBusClient

    bus = InMemoryBusClient()
    radar = CatalystRadarAgent(event_bus=bus)

    received = []
    async def handler(event):
        received.append(event)
    await bus.subscribe("ai:news:catalyst_radar", handler)

    radar.add_catalyst(CatalystEvent(
        event_id="c1", name="FOMC",
        scheduled_time=datetime.now(timezone.utc) + timedelta(days=1),
        category=NewsCategory.FED,
        importance=EventImportance.CRITICAL,
    ))
    await radar.publish_radar()

    assert len(received) == 1
    await bus.close()


# ============================================================================
# Exit Criteria 7: 4 Intelligence Objects established
# ============================================================================

async def test_4_intelligence_objects():
    """By end of Stage 10, 4 intelligence objects exist:
    1. Technical DNA (Stage 7)
    2. Options DNA (Stage 8)
    3. Market DNA (Stage 9)
    4. Narrative DNA (Stage 10)
    """
    # Narrative DNA is the 4th object
    agent = NarrativeDNAAgent()
    agent.add_raw_article({"headline": "CPI higher", "source": "Reuters"})
    dna = await agent.compute_narrative()

    # Has all required fields for downstream AI consumption
    assert hasattr(dna, "primary_driver")
    assert hasattr(dna, "current_theme")
    assert hasattr(dna, "confidence")
    assert hasattr(dna, "story_of_the_day")
    assert hasattr(dna, "impact_summary")
    assert hasattr(dna, "event_timeline")
    assert hasattr(dna, "upcoming_catalysts")
    assert hasattr(dna, "active_events")


# ============================================================================
# Exit Criteria 8: Downstream consumes Narrative DNA (not raw news)
# ============================================================================

async def test_downstream_consumes_narrative_not_raw():
    """Downstream stages consume NarrativeDNA, not raw news articles."""
    agent = NarrativeDNAAgent()
    agent.add_raw_article({"headline": "CPI 3.2%", "source": "Reuters"})
    agent.add_raw_article({"headline": "Fed hawkish", "source": "Bloomberg"})
    agent.add_raw_article({"headline": "NVDA beats", "source": "CNBC"})

    dna = await agent.compute_narrative()

    # Downstream gets a single object with:
    # - primary_driver (string)
    # - theme (string)
    # - confidence (float)
    # - story (string)
    # - impact_summary (dict)
    # - timeline (list)
    # NOT 3 separate raw articles
    assert isinstance(dna.primary_driver, str)
    assert isinstance(dna.current_theme, str)
    assert isinstance(dna.confidence, float)
    assert isinstance(dna.story_of_the_day, str)
    assert isinstance(dna.impact_summary, dict)
    assert isinstance(dna.event_timeline, list)
''')

print(f"\\n✅ Stage 10 complete: {len(FILES)} files written")
print("\\nComponents implemented:")
print("  1. plugins/news/_base/ - NewsPlugin Protocol + NarrativeDNA + CatalystEvent types")
print("  2. plugins/news/*/manifest.yaml - 10 news category manifests")
print("  3. engines/narrative-engine/ - Event Classifier + Impact Engine + Timeline + Narrative Generator")
print("  4. agents/narrative-intelligence/ - Narrative DNA Agent + Catalyst Radar Agent")
print("  5. runtime/stage10-integration/ - 8 exit criteria acceptance tests")
print("\\nNext: install deps and run tests")
