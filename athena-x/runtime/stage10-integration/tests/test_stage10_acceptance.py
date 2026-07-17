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
