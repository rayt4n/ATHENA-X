"""Adapter Registry — registers every discovered agent as an AdapterManifest.

This is the bridge between the runtime agent architecture and the legacy
PluginRegistry. PluginRegistry sees a uniform set of "plugins" via the
adapter manifests; the adapter layer delegates execution to the real
runtime agents.
"""
from __future__ import annotations
from threading import RLock
from typing import Any
from athena_x_runtime_logger import get_logger

from ..discovery import RuntimeDiscovery, DiscoveredAgent
from .base import AgentAdapter, adapt_agent

log = get_logger("institutional-workspace.registry")


class AdapterRegistry:
    """Registry of adapted runtime agents.

    Usage:
        registry = AdapterRegistry()
        registry.discover_and_register()
        adapter = registry.get("ta.ema")
        result = await adapter.execute("SPY", Timeframe.FIFTEEN_MIN, repo)
    """

    def __init__(self):
        self._adapters: dict[str, AgentAdapter] = {}
        self._lock = RLock()
        self._discovery = RuntimeDiscovery()

    def discover_and_register(self) -> int:
        """Discover all runtime agents and register them as adapters."""
        discovered = self._discovery.discover_all()
        count = 0
        with self._lock:
            for d in discovered:
                try:
                    adapter = adapt_agent(d)
                    self._adapters[adapter.agent_id] = adapter
                    count += 1
                except Exception as e:
                    log.warning("adapter_register_failed",
                                agent_id=d.agent_id, error=str(e))
        log.info("adapters_registered", count=count)
        return count

    def get(self, agent_id: str) -> AgentAdapter | None:
        with self._lock:
            return self._adapters.get(agent_id)

    def list_all(self) -> list[AgentAdapter]:
        with self._lock:
            return list(self._adapters.values())

    def list_by_layer(self, layer: int | str) -> list[AgentAdapter]:
        with self._lock:
            return [a for a in self._adapters.values() if a.layer == layer]

    def list_by_category(self, category: str) -> list[AgentAdapter]:
        with self._lock:
            return [a for a in self._adapters.values() if a.category == category]

    def list_manifests(self) -> list[dict]:
        """Return list of manifest dicts (for PluginRegistry compatibility)."""
        with self._lock:
            return [a.manifest.to_dict() for a in self._adapters.values()]

    def count(self) -> int:
        with self._lock:
            return len(self._adapters)

    def get_summary(self) -> dict:
        agents = self.list_all()
        by_layer: dict[str, int] = {}
        by_category: dict[str, int] = {}
        for a in agents:
            key = str(a.layer)
            by_layer[key] = by_layer.get(key, 0) + 1
            by_category[a.category] = by_category.get(a.category, 0) + 1
        return {
            "total_adapters": len(agents),
            "by_layer": by_layer,
            "by_category": by_category,
        }
