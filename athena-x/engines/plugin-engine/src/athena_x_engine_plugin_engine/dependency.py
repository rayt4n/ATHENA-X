"""Dependency Manager - resolves calculation dependencies.

Instead of recalculating, the Dependency Manager provides existing results.

Example:
  MACD -> EMA -> OHLCV
  Wyckoff -> Volume Profile -> Volume

Dependencies are resolved automatically.
"""
from __future__ import annotations
from collections import defaultdict, deque
from dataclasses import dataclass, field
from threading import RLock
from typing import Any
from athena_x_runtime_logger import get_logger

from .registry import PluginRegistry

log = get_logger("plugin.dependency")


@dataclass
class DependencyGraph:
    """Directed graph of plugin dependencies."""
    edges: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    reverse_edges: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))

    def add_dependency(self, plugin_id: str, depends_on: str) -> None:
        """Add: plugin_id depends on depends_on."""
        self.edges[plugin_id].append(depends_on)
        self.reverse_edges[depends_on].append(plugin_id)

    def get_dependencies(self, plugin_id: str) -> list[str]:
        """Get direct dependencies of a plugin."""
        return self.edges.get(plugin_id, [])

    def get_dependents(self, plugin_id: str) -> list[str]:
        """Get plugins that depend on this plugin."""
        return self.reverse_edges.get(plugin_id, [])

    def topological_sort(self, plugin_ids: list[str]) -> list[str]:
        """Return plugins in dependency order (dependencies first)."""
        in_degree: dict[str, int] = {pid: 0 for pid in plugin_ids}
        queue: deque[str] = deque()

        for pid in plugin_ids:
            deps = self.get_dependencies(pid)
            for dep in deps:
                if dep in in_degree:
                    in_degree[pid] += 1

        for pid in plugin_ids:
            if in_degree[pid] == 0:
                queue.append(pid)

        result: list[str] = []
        while queue:
            current = queue.popleft()
            result.append(current)
            for dependent in self.get_dependents(current):
                if dependent in in_degree:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        queue.append(dependent)

        return result

    def detect_cycles(self) -> list[list[str]]:
        """Detect circular dependencies."""
        visited: set[str] = set()
        rec_stack: set[str] = set()
        cycles: list[list[str]] = []

        def dfs(node: str, path: list[str]) -> None:
            if node in rec_stack:
                cycle_start = path.index(node) if node in path else 0
                cycles.append(path[cycle_start:] + [node])
                return
            if node in visited:
                return
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            for dep in self.edges.get(node, []):
                dfs(dep, path)
            path.pop()
            rec_stack.discard(node)

        for node in list(self.edges.keys()):
            if node not in visited:
                dfs(node, [])

        return cycles


class DependencyResolver:
    """Resolves calculation dependencies.

    Usage:
        resolver = DependencyResolver(registry)
        order = resolver.get_execution_order()  # topological sort
        deps = resolver.get_dependencies("macd")  # ["ema"]
    """

    def __init__(self, registry: PluginRegistry):
        self._registry = registry
        self._graph = DependencyGraph()
        self._lock = RLock()
        self._results: dict[str, Any] = {}  # cached results by plugin_id
        self._build_graph()

    def _build_graph(self) -> None:
        """Build the dependency graph from registered plugins."""
        for entry in self._registry.list_all():
            for dep in entry.manifest.dependencies:
                self._graph.add_dependency(entry.manifest.id, dep)

    def get_execution_order(self) -> list[str]:
        """Get the order in which plugins should be executed (dependencies first)."""
        plugin_ids = [e.manifest.id for e in self._registry.list_enabled()]
        return self._graph.topological_sort(plugin_ids)

    def get_dependencies(self, plugin_id: str) -> list[str]:
        """Get the dependencies of a plugin."""
        return self._graph.get_dependencies(plugin_id)

    def get_dependents(self, plugin_id: str) -> list[str]:
        """Get plugins that depend on this plugin."""
        return self._graph.get_dependents(plugin_id)

    def get_result(self, plugin_id: str) -> Any:
        """Get a cached result from a dependency."""
        with self._lock:
            return self._results.get(plugin_id)

    def set_result(self, plugin_id: str, result: Any) -> None:
        """Cache a result for use by dependent plugins."""
        with self._lock:
            self._results[plugin_id] = result

    def detect_cycles(self) -> list[list[str]]:
        """Detect circular dependencies."""
        return self._graph.detect_cycles()

    def get_stats(self) -> dict:
        return {
            "total_edges": sum(len(deps) for deps in self._graph.edges.values()),
            "cached_results": len(self._results),
            "cycles_detected": len(self.detect_cycles()),
        }
