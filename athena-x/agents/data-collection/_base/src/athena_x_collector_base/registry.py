"""Collector registry — tracks all running collectors."""
from __future__ import annotations
from typing import Iterator
from threading import Lock

from .base import BaseCollector


class CollectorRegistry:
    """Thread-safe registry of running collectors."""

    def __init__(self):
        self._collectors: dict[str, BaseCollector] = {}
        self._lock = Lock()

    def register(self, collector: BaseCollector) -> None:
        with self._lock:
            self._collectors[collector.collector_id] = collector

    def unregister(self, collector_id: str) -> None:
        with self._lock:
            self._collectors.pop(collector_id, None)

    def get(self, collector_id: str) -> BaseCollector | None:
        with self._lock:
            return self._collectors.get(collector_id)

    def list_all(self) -> list[BaseCollector]:
        with self._lock:
            return list(self._collectors.values())

    def list_by_symbol(self, symbol: str) -> list[BaseCollector]:
        with self._lock:
            return [c for c in self._collectors.values() if c.symbol == symbol]

    def stats(self) -> list[dict]:
        with self._lock:
            return [c.get_stats() for c in self._collectors.values()]

    def __iter__(self) -> Iterator[BaseCollector]:
        return iter(self.list_all())
