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
