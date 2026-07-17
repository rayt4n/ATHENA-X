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
