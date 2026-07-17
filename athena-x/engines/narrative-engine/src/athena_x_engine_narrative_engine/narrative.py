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
