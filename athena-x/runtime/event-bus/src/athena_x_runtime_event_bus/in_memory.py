"""In-memory bus client for tests and development (no external deps)."""
from __future__ import annotations
import asyncio
import logging
from collections import defaultdict
from typing import Dict, Set
import time

from .types import BusEvent, BusClient, EventHandler, pattern_matches

_log = logging.getLogger("athena_x.event_bus.in_memory")


class InMemoryBusClient(BusClient):
    """In-process pub/sub. Used in tests and dev (no Redis/NATS required)."""

    def __init__(self, backpressure_max_age_ms: int = 500):
        self._handlers: Dict[str, Set[EventHandler]] = defaultdict(set)
        self._backpressure_max_age_ms = backpressure_max_age_ms
        self._closed = False
        self._publish_count = 0
        self._drop_count = 0

    async def publish(self, event: BusEvent) -> None:
        if self._closed:
            raise RuntimeError("Bus is closed")

        # Backpressure: drop stale market data events
        if (event.event_type.startswith("market:")
                and self._backpressure_max_age_ms > 0):
            age_ms = (time.time() - event.timestamp.timestamp()) * 1000
            if age_ms > self._backpressure_max_age_ms:
                self._drop_count += 1
                return

        self._publish_count += 1

        # Dispatch to all matching handlers
        matching: list[EventHandler] = []
        for pattern, handlers in self._handlers.items():
            if pattern_matches(pattern, event.event_type):
                matching.extend(handlers)

        # Dispatch concurrently, but surface exceptions
        if matching:
            results = await asyncio.gather(
                *(h(event) for h in matching),
                return_exceptions=True,
            )
            for r in results:
                if isinstance(r, Exception):
                    _log.error("handler_failed: %s", r, exc_info=r)

    async def subscribe(self, pattern: str, handler: EventHandler) -> None:
        self._handlers[pattern].add(handler)

    async def unsubscribe(self, pattern: str, handler: EventHandler) -> None:
        self._handlers[pattern].discard(handler)

    async def close(self) -> None:
        self._closed = True
        self._handlers.clear()

    async def health_check(self) -> bool:
        return not self._closed

    @property
    def publish_count(self) -> int:
        return self._publish_count

    @property
    def drop_count(self) -> int:
        return self._drop_count
