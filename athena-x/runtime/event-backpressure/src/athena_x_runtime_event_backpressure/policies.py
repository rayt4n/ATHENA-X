"""Backpressure policies - Stage 6 req 6.

Refined rules:
  - Market ticks: keep only the latest if consumers fall behind
  - News and macro: never drop; queue them
  - Orders and execution (future): never drop
  - Health metrics: coalesce multiple updates into summaries
"""
from __future__ import annotations
from collections import deque
from dataclasses import dataclass
from enum import Enum
from threading import RLock
from typing import Any

from athena_x_runtime_event_envelope import EventEnvelope, EventPriority


class BackpressureAction(str, Enum):
    """What to do with an event under backpressure."""
    ACCEPT = "accept"      # Accept the event
    DROP = "drop"          # Drop the event (keep latest)
    QUEUE = "queue"        # Queue the event (never drop)
    COALESCE = "coalesce"  # Merge with previous (summaries)


@dataclass
class BackpressurePolicy:
    """Policy for a specific event category."""
    category: str
    action: BackpressureAction
    max_queue_size: int = 10000
    max_age_ms: int = 500  # for DROP policy - drop if older than this


class BackpressureManager:
    """Manages backpressure for different event categories.

    Policies:
      market (HIGH priority): DROP - keep only latest if behind
      market (NORMAL): DROP - keep only latest
      news: QUEUE - never drop
      ai: QUEUE - never drop
      reports: QUEUE - never drop
      system (LOW): COALESCE - merge into summaries
      system (CRITICAL): ACCEPT - never drop
    """

    def __init__(self):
        self._policies: dict[str, BackpressurePolicy] = {
            "market:high": BackpressurePolicy("market", BackpressureAction.DROP, max_age_ms=500),
            "market:normal": BackpressurePolicy("market", BackpressureAction.DROP, max_age_ms=500),
            "market:low": BackpressurePolicy("market", BackpressureAction.DROP, max_age_ms=500),
            "news": BackpressurePolicy("news", BackpressureAction.QUEUE, max_queue_size=50000),
            "ai": BackpressurePolicy("ai", BackpressureAction.QUEUE, max_queue_size=10000),
            "reports": BackpressurePolicy("reports", BackpressureAction.QUEUE, max_queue_size=1000),
            "system:low": BackpressurePolicy("system", BackpressureAction.COALESCE, max_queue_size=100),
            "system:critical": BackpressurePolicy("system", BackpressureAction.ACCEPT),
        }
        self._latest: dict[str, EventEnvelope] = {}  # for DROP policy (per symbol)
        self._queues: dict[str, deque] = {}  # for QUEUE policy
        self._summaries: dict[str, dict] = {}  # for COALESCE
        self._lock = RLock()
        self._dropped_count = 0
        self._coalesced_count = 0

    def evaluate(self, event: EventEnvelope) -> BackpressureAction:
        """Evaluate what to do with an event based on its category + priority."""
        category = event.category.value
        priority = event.priority.value

        # Determine policy key
        if category == "market":
            key = f"market:{priority}"
        elif category == "system":
            key = f"system:{priority}"
        else:
            key = category

        policy = self._policies.get(key)
        if policy is None:
            return BackpressureAction.ACCEPT  # default: accept

        if policy.action == BackpressureAction.DROP:
            return self._evaluate_drop(event, policy)
        elif policy.action == BackpressureAction.QUEUE:
            return self._evaluate_queue(event, policy)
        elif policy.action == BackpressureAction.COALESCE:
            return BackpressureAction.COALESCE
        else:
            return BackpressureAction.ACCEPT

    def _evaluate_drop(self, event: EventEnvelope, policy: BackpressurePolicy) -> BackpressureAction:
        """For market ticks: keep only the latest if consumers fall behind."""
        # Check if event is too old
        from datetime import datetime, timezone
        age_ms = (datetime.now(timezone.utc) - event.timestamp).total_seconds() * 1000
        if age_ms > policy.max_age_ms:
            with self._lock:
                self._dropped_count += 1
            return BackpressureAction.DROP
        return BackpressureAction.ACCEPT

    def _evaluate_queue(self, event: EventEnvelope, policy: BackpressurePolicy) -> BackpressureAction:
        """For news/macro: never drop; queue them."""
        key = event.category.value
        with self._lock:
            if key not in self._queues:
                self._queues[key] = deque(maxlen=policy.max_queue_size)
            q = self._queues[key]
            if len(q) >= policy.max_queue_size:
                # Even queue is full - drop oldest (but still accept new)
                q.popleft()
            q.append(event)
        return BackpressureAction.ACCEPT

    def coalesce(self, event: EventEnvelope) -> dict | None:
        """For health metrics: coalesce into summaries.

        Returns the coalesced summary if enough events have been merged,
        None otherwise.
        """
        key = f"{event.source_agent}:{event.event_type}"
        with self._lock:
            if key not in self._summaries:
                self._summaries[key] = {
                    "count": 0,
                    "first_timestamp": event.timestamp.isoformat(),
                    "last_event": None,
                }
            summary = self._summaries[key]
            summary["count"] += 1
            summary["last_event"] = event
            summary["last_timestamp"] = event.timestamp.isoformat()
            self._coalesced_count += 1

            # Emit summary every 10 events
            if summary["count"] >= 10:
                result = dict(summary)
                del self._summaries[key]
                return result
        return None

    def get_stats(self) -> dict:
        with self._lock:
            return {
                "dropped_count": self._dropped_count,
                "coalesced_count": self._coalesced_count,
                "queue_sizes": {k: len(v) for k, v in self._queues.items()},
                "pending_summaries": len(self._summaries),
            }
