"""Event monitor - Stage 6 req 8.

Dashboard showing:
  - Events/sec
  - Queue depth
  - Average latency
  - Slowest consumers
  - Dropped events
  - Failed events
  - Retry count
  - Dead-letter queue size
  - Active agents
  - Provider latency
"""
from __future__ import annotations
import statistics
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import RLock
from typing import Deque

from athena_x_runtime_event_envelope import EventEnvelope


@dataclass
class ConsumerStats:
    """Statistics for a single consumer (subscriber)."""
    consumer_id: str
    events_processed: int = 0
    errors: int = 0
    retries: int = 0
    latencies: Deque[float] = field(default_factory=lambda: deque(maxlen=1000))
    last_processed: datetime | None = None

    @property
    def avg_latency_ms(self) -> float:
        return statistics.mean(self.latencies) if self.latencies else 0.0

    @property
    def p99_latency_ms(self) -> float:
        if not self.latencies:
            return 0.0
        sorted_l = sorted(self.latencies)
        return sorted_l[int(len(sorted_l) * 0.99)]

    @property
    def error_rate(self) -> float:
        return self.errors / self.events_processed if self.events_processed > 0 else 0.0


@dataclass
class EventMonitorMetrics:
    """Aggregated metrics for the event monitoring dashboard."""
    events_per_sec: float = 0.0
    total_events_published: int = 0
    total_events_processed: int = 0
    total_events_dropped: int = 0
    total_events_failed: int = 0
    total_retries: int = 0
    queue_depth: int = 0
    dead_letter_queue_size: int = 0
    active_agents: int = 0
    avg_latency_ms: float = 0.0
    slowest_consumers: list[dict] = field(default_factory=list)
    by_category: dict[str, int] = field(default_factory=dict)
    by_priority: dict[str, int] = field(default_factory=dict)


class EventMonitor:
    """Monitors event bus performance.

    Usage:
        monitor = EventMonitor()
        monitor.record_publish(event)
        monitor.record_process("consumer-1", event, latency_ms=5.0)
        metrics = monitor.get_metrics()
    """

    def __init__(self, window_seconds: int = 60):
        self._window = window_seconds
        self._publish_times: deque[float] = deque(maxlen=10000)
        self._lock = RLock()
        self._total_published = 0
        self._total_dropped = 0
        self._total_failed = 0
        self._total_retries = 0
        self._dead_letter_count = 0
        self._consumers: dict[str, ConsumerStats] = {}
        self._by_category: dict[str, int] = defaultdict(int)
        self._by_priority: dict[str, int] = defaultdict(int)
        self._active_agents: set[str] = set()
        self._start_time = time.monotonic()

    def record_publish(self, event: EventEnvelope) -> None:
        """Record that an event was published."""
        with self._lock:
            self._total_published += 1
            self._publish_times.append(time.monotonic())
            self._by_category[event.category.value] += 1
            self._by_priority[event.priority.value] += 1
            self._active_agents.add(event.source_agent)

    def record_process(self, consumer_id: str, event: EventEnvelope, latency_ms: float, success: bool = True) -> None:
        """Record that a consumer processed an event."""
        with self._lock:
            if consumer_id not in self._consumers:
                self._consumers[consumer_id] = ConsumerStats(consumer_id=consumer_id)
            stats = self._consumers[consumer_id]
            stats.events_processed += 1
            stats.latencies.append(latency_ms)
            stats.last_processed = datetime.now(timezone.utc)
            if not success:
                stats.errors += 1

    def record_drop(self) -> None:
        with self._lock:
            self._total_dropped += 1

    def record_failure(self) -> None:
        with self._lock:
            self._total_failed += 1

    def record_retry(self) -> None:
        with self._lock:
            self._total_retries += 1

    def record_dead_letter(self) -> None:
        with self._lock:
            self._dead_letter_count += 1

    def get_metrics(self) -> EventMonitorMetrics:
        """Get current metrics for the dashboard."""
        with self._lock:
            now = time.monotonic()
            # Calculate events/sec over the window
            recent = [t for t in self._publish_times if now - t < self._window]
            events_per_sec = len(recent) / self._window if recent else 0.0

            # Find slowest consumers
            consumers = list(self._consumers.values())
            slowest = sorted(consumers, key=lambda c: c.p99_latency_ms, reverse=True)[:5]

            # Average latency across all consumers
            all_latencies = []
            for c in consumers:
                all_latencies.extend(c.latencies)
            avg_latency = statistics.mean(all_latencies) if all_latencies else 0.0

            return EventMonitorMetrics(
                events_per_sec=events_per_sec,
                total_events_published=self._total_published,
                total_events_processed=sum(c.events_processed for c in self._consumers.values()),
                total_events_dropped=self._total_dropped,
                total_events_failed=self._total_failed,
                total_retries=self._total_retries,
                dead_letter_queue_size=self._dead_letter_count,
                active_agents=len(self._active_agents),
                avg_latency_ms=avg_latency,
                slowest_consumers=[
                    {
                        "consumer_id": c.consumer_id,
                        "p99_latency_ms": c.p99_latency_ms,
                        "events_processed": c.events_processed,
                        "error_rate": c.error_rate,
                    }
                    for c in slowest
                ],
                by_category=dict(self._by_category),
                by_priority=dict(self._by_priority),
            )
