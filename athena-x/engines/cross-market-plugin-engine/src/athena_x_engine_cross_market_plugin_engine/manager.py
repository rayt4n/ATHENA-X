"""Cross-Market Plugin Manager - discovers + loads cross-market plugins.

Reuses the Stage 7 plugin engine infrastructure.
The engine doesn't know which correlations or leadership signals exist.
It only loads plugins.
"""
from __future__ import annotations
from pathlib import Path
from athena_x_engine_plugin_engine import PluginManager
from athena_x_runtime_logger import get_logger

log = get_logger("cross-market-plugin-engine")


class CrossMarketPluginManager:
    """Manages cross-market intelligence plugins.

    Wraps the Stage 7 PluginManager with cross-market-specific defaults.
    """

    def __init__(self, plugin_dir: str | Path = "plugins/cross-market"):
        self._inner = PluginManager(plugin_dir=plugin_dir)
        self._registry = self._inner.registry

    @property
    def registry(self):
        return self._registry

    @property
    def dependency_resolver(self):
        return self._inner.dependency_resolver

    @property
    def scheduler(self):
        return self._inner.scheduler

    @property
    def config_service(self):
        return self._inner.config_service

    def discover(self) -> int:
        return self._inner.discover()

    def load_all(self) -> int:
        return self._inner.load_all()

    def load(self, plugin_id: str):
        return self._inner.load(plugin_id)

    def get_instance(self, plugin_id: str):
        return self._inner.get_instance(plugin_id)

    def list_by_category(self, category: str) -> list:
        return [
            e for e in self._registry.list_all()
            if e.manifest.category.value == category
        ]

    def get_stats(self) -> dict:
        stats = self._inner.get_stats()
        from collections import Counter
        categories = Counter()
        for entry in self._registry.list_all():
            categories[entry.manifest.category.value] += 1
        stats["by_category"] = dict(categories)
        return stats
