"""Priority queue - Stage 6 req 3.

4 levels: critical > high > normal > low

Under heavy load, low-priority events can be delayed without affecting
trading intelligence.
"""
from __future__ import annotations
import asyncio
from collections import deque
from dataclasses import dataclass, field
from threading import RLock
from typing import Any

from athena_x_runtime_event_envelope import EventEnvelope, EventPriority


@dataclass
class QueueStats:
    """Statistics for a priority queue."""
    critical_count: int = 0
    high_count: int = 0
    normal_count: int = 0
    low_count: int = 0
    total_enqueued: int = 0
    total_dequeued: int = 0
    total_dropped: int = 0

    @property
    def total_pending(self) -> int:
        return self.critical_count + self.high_count + self.normal_count + self.low_count


class PriorityQueue:
    """4-level priority queue for events.

    Dequeue order: critical first, then high, normal, low.
    Each level is FIFO within the level.

    Usage:
        q = PriorityQueue(max_size=10000)
        await q.enqueue(event)
        event = await q.dequeue()
    """

    def __init__(self, max_size_per_level: int = 10000):
        self._queues: dict[EventPriority, deque] = {
            EventPriority.CRITICAL: deque(),
            EventPriority.HIGH: deque(),
            EventPriority.NORMAL: deque(),
            EventPriority.LOW: deque(),
        }
        self._max_size = max_size_per_level
        self._lock = RLock()
        self._not_empty = asyncio.Event()
        self._stats = QueueStats()

    async def enqueue(self, event: EventEnvelope) -> bool:
        """Enqueue an event. Returns False if dropped (queue full)."""
        with self._lock:
            q = self._queues[event.priority]
            if len(q) >= self._max_size:
                # Drop based on priority policy
                if event.priority == EventPriority.LOW:
                    self._stats.total_dropped += 1
                    return False
                elif event.priority == EventPriority.NORMAL:
                    # Drop oldest normal event to make room
                    if q:
                        q.popleft()
                        self._stats.total_dropped += 1
                # critical and high are never dropped

            q.append(event)
            self._stats.total_enqueued += 1
            self._update_counts()

        self._not_empty.set()
        return True

    async def dequeue(self, timeout: float | None = None) -> EventEnvelope | None:
        """Dequeue the highest-priority event. Returns None if timeout."""
        import time
        start = time.monotonic()

        while True:
            with self._lock:
                for priority in [EventPriority.CRITICAL, EventPriority.HIGH,
                                 EventPriority.NORMAL, EventPriority.LOW]:
                    q = self._queues[priority]
                    if q:
                        event = q.popleft()
                        self._stats.total_dequeued += 1
                        self._update_counts()
                        return event

                if not self._not_empty.is_set():
                    self._not_empty.clear()

            if timeout is not None and (time.monotonic() - start) > timeout:
                return None

            await asyncio.sleep(0.001)

    def _update_counts(self) -> None:
        self._stats.critical_count = len(self._queues[EventPriority.CRITICAL])
        self._stats.high_count = len(self._queues[EventPriority.HIGH])
        self._stats.normal_count = len(self._queues[EventPriority.NORMAL])
        self._stats.low_count = len(self._queues[EventPriority.LOW])

    def get_stats(self) -> QueueStats:
        with self._lock:
            self._update_counts()
            return self._stats

    @property
    def size(self) -> int:
        with self._lock:
            return sum(len(q) for q in self._queues.values())
