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
        "headline": "TSMC reports strong chip demand from NVDA",
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
