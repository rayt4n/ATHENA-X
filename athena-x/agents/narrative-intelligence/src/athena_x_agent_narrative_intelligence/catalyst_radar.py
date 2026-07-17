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
