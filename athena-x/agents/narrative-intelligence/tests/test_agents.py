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
