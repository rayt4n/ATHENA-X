"""Plugin Manager - discovers, loads, unloads, and validates indicator plugins.

The engine never knows which indicators exist. It only knows how to load plugins.

Usage:
    manager = PluginManager(plugin_dir="plugins/indicators")
    manager.discover()  # scans for manifest.yaml files
    manager.load_all()  # loads all discovered plugins
    manager.execute("ema", symbol="SPY", timeframe="15m", data=...)
"""
from __future__ import annotations
import importlib
import importlib.util
import sys
from pathlib import Path
from threading import RLock
from typing import Any
from athena_x_runtime_logger import get_logger

from .manifest import PluginManifest
from .registry import PluginRegistry
from .dependency import DependencyResolver
from .scheduler import PluginScheduler
from .config import PluginConfigService

log = get_logger("plugin.manager")


class PluginManager:
    """Discovers, loads, and manages indicator plugins.

    The engine never knows which indicators exist.
    It only knows how to load plugins from the plugins/ directory.

    Adding a new indicator = adding a new folder with manifest.yaml + indicator.py
    No existing code needs to change.
    """

    def __init__(
        self,
        plugin_dir: str | Path = "plugins/indicators",
        registry: PluginRegistry | None = None,
    ):
        self._plugin_dir = Path(plugin_dir)
        self._registry = registry or PluginRegistry()
        self._dependency_resolver = DependencyResolver(self._registry)
        self._scheduler = PluginScheduler(self._registry)
        self._config_service = PluginConfigService(self._registry)
        self._lock = RLock()
        self._loaded: dict[str, Any] = {}  # plugin_id -> TechnicalIndicator instance

    @property
    def registry(self) -> PluginRegistry:
        return self._registry

    @property
    def dependency_resolver(self) -> DependencyResolver:
        return self._dependency_resolver

    @property
    def scheduler(self) -> PluginScheduler:
        return self._scheduler

    @property
    def config_service(self) -> PluginConfigService:
        return self._config_service

    def discover(self) -> int:
        """Scan the plugin directory for manifest.yaml files.

        Returns the number of plugins discovered.
        """
        count = 0
        if not self._plugin_dir.exists():
            log.warning("plugin_dir_not_found", path=str(self._plugin_dir))
            return 0

        for plugin_path in self._plugin_dir.iterdir():
            if not plugin_path.is_dir():
                continue
            if plugin_path.name.startswith("_") or plugin_path.name.startswith("."):
                continue  # skip _base and hidden dirs

            manifest_path = plugin_path / "manifest.yaml"
            if not manifest_path.exists():
                continue

            try:
                manifest = PluginManifest.from_yaml(str(manifest_path))
                self._registry.register(manifest, str(plugin_path))
                count += 1
            except Exception as e:
                log.error("plugin_discover_failed",
                          path=str(plugin_path),
                          error=str(e))

        log.info("plugins_discovered", count=count)
        # Rebuild dependency graph + scheduler after discovery
        self._dependency_resolver = DependencyResolver(self._registry)
        self._scheduler.rebuild()
        return count

    def load(self, plugin_id: str) -> Any:
        """Load a specific plugin by ID.

        Dynamically imports the indicator module and instantiates it.
        """
        with self._lock:
            if plugin_id in self._loaded:
                return self._loaded[plugin_id]

            entry = self._registry.get(plugin_id)
            if entry is None:
                raise ValueError(f"Plugin not found: {plugin_id}")

            plugin_path = Path(entry.plugin_path)
            module_name = f"athena_x_plugin_indicators_{plugin_id.replace('-', '_')}"

            # Try to import the module
            try:
                # First try installed package
                module = importlib.import_module(module_name)
            except ImportError:
                # Try loading from file
                indicator_file = plugin_path / "src" / module_name / "indicator.py"
                if not indicator_file.exists():
                    indicator_file = plugin_path / "indicator.py"
                if not indicator_file.exists():
                    raise ImportError(f"Cannot find indicator.py for plugin {plugin_id}")

                spec = importlib.util.spec_from_file_location(module_name, indicator_file)
                if spec is None or spec.loader is None:
                    raise ImportError(f"Cannot load module for plugin {plugin_id}")
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)

            # Find the indicator class
            # Convention: class name is PluginId + "Indicator" or PluginId + "Agent"
            class_candidates = [
                plugin_id.title().replace("-", "") + "Indicator",
                plugin_id.title().replace("-", "") + "Agent",
                plugin_id.upper() + "Indicator",
                "Indicator",
            ]
            instance = None
            for class_name in class_candidates:
                if hasattr(module, class_name):
                    cls = getattr(module, class_name)
                    instance = cls()
                    break

            if instance is None:
                # Try to find any class that looks like an indicator
                for name in dir(module):
                    obj = getattr(module, name)
                    if isinstance(obj, type) and name != "Indicator" and not name.startswith("_"):
                        instance = obj()
                        break

            if instance is None:
                raise ImportError(f"Cannot find indicator class in plugin {plugin_id}")

            self._loaded[plugin_id] = instance
            self._registry.set_loaded(plugin_id, instance)
            log.info("plugin_loaded", plugin_id=plugin_id)
            return instance

    def load_all(self) -> int:
        """Load all enabled plugins. Returns count loaded."""
        count = 0
        for entry in self._registry.list_enabled():
            try:
                self.load(entry.manifest.id)
                count += 1
            except Exception as e:
                log.error("plugin_load_failed",
                          plugin_id=entry.manifest.id,
                          error=str(e))
        log.info("plugins_loaded", count=count)
        return count

    def unload(self, plugin_id: str) -> None:
        """Unload a plugin."""
        with self._lock:
            self._loaded.pop(plugin_id, None)
            entry = self._registry.get(plugin_id)
            if entry:
                entry.loaded = False
                entry.instance = None
            log.info("plugin_unloaded", plugin_id=plugin_id)

    def reload(self, plugin_id: str) -> Any:
        """Hot-reload a plugin (unload + load)."""
        self.unload(plugin_id)
        return self.load(plugin_id)

    def get_instance(self, plugin_id: str) -> Any:
        """Get the loaded instance of a plugin."""
        with self._lock:
            return self._loaded.get(plugin_id)

    def list_loaded(self) -> list[str]:
        """List all loaded plugin IDs."""
        with self._lock:
            return list(self._loaded.keys())

    def get_stats(self) -> dict:
        return {
            "discovered": self._registry.count(),
            "enabled": self._registry.count_enabled(),
            "loaded": len(self._loaded),
            "categories": [c.value for c in self._registry.get_categories()],
            "dependency_stats": self._dependency_resolver.get_stats(),
            "scheduler_stats": self._scheduler.get_stats(),
        }
