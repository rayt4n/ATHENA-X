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
