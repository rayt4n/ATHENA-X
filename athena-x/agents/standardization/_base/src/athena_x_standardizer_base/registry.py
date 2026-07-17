"""Standardizer registry — tracks all standardization agents."""
from __future__ import annotations
from threading import RLock
from typing import Callable


class StandardizerRegistry:
    """Registry of standardization agent factories."""
    def __init__(self):
        self._factories: dict[str, Callable] = {}
        self._lock = RLock()

    def register(self, name: str, factory: Callable) -> None:
        with self._lock:
            self._factories[name] = factory

    def get(self, name: str) -> Callable | None:
        with self._lock:
            return self._factories.get(name)

    def list_all(self) -> list[str]:
        with self._lock:
            return list(self._factories.keys())
