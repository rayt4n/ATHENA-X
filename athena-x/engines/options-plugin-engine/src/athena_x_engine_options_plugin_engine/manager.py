"""Options Plugin Manager - discovers + loads options metric plugins.

Reuses the Stage 7 plugin engine infrastructure (PluginManager, Registry,
DependencyResolver, Scheduler, ConfigService) but pointed at the options
plugins directory.

The engine doesn't know about Gamma Flip, Max Pain, or IV Rank directly.
It only loads plugins.
"""
from __future__ import annotations
from pathlib import Path
from athena_x_engine_plugin_engine import (
    PluginManager, PluginRegistry, PluginManifest, PluginCategory,
    DependencyResolver, PluginScheduler, PluginConfigService,
)
from athena_x_runtime_logger import get_logger

log = get_logger("options-plugin-engine")


class OptionsPluginManager:
    """Manages options metric plugins.

    Wraps the Stage 7 PluginManager with options-specific defaults.

    Usage:
        mgr = OptionsPluginManager(plugin_dir="plugins/options")
        mgr.discover()  # finds all manifest.yaml files
        mgr.load_all()  # loads all enabled plugins
        stats = mgr.get_stats()
    """

    def __init__(self, plugin_dir: str | Path = "plugins/options"):
        self._inner = PluginManager(plugin_dir=plugin_dir)
        # Override the category enum mapping for options-specific categories
        self._registry = self._inner.registry

    @property
    def registry(self) -> PluginRegistry:
        return self._registry

    @property
    def dependency_resolver(self) -> DependencyResolver:
        return self._inner.dependency_resolver

    @property
    def scheduler(self) -> PluginScheduler:
        return self._inner.scheduler

    @property
    def config_service(self) -> PluginConfigService:
        return self._inner.config_service

    def discover(self) -> int:
        """Discover all options plugins from manifest.yaml files."""
        return self._inner.discover()

    def load_all(self) -> int:
        """Load all enabled plugins."""
        return self._inner.load_all()

    def load(self, plugin_id: str):
        """Load a specific plugin."""
        return self._inner.load(plugin_id)

    def get_instance(self, plugin_id: str):
        """Get a loaded plugin instance."""
        return self._inner.get_instance(plugin_id)

    def list_by_category(self, category: str) -> list:
        """List plugins by options category (string match, no enum dependency)."""
        return [
            e for e in self._registry.list_all()
            if e.manifest.category.value == category
        ]

    def get_stats(self) -> dict:
        """Get comprehensive stats."""
        stats = self._inner.get_stats()
        # Add options-specific category breakdown
        from collections import Counter
        categories = Counter()
        for entry in self._registry.list_all():
            categories[entry.manifest.category.value] += 1
        stats["by_category"] = dict(categories)
        return stats
