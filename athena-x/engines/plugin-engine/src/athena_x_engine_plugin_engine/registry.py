"""Indicator Registry - maintains metadata, versions, and capabilities of installed plugins.

Adding an indicator only means adding another folder.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from threading import RLock
from typing import Any
from athena_x_runtime_logger import get_logger

from .manifest import PluginManifest, PluginCategory

log = get_logger("plugin.registry")


@dataclass
class RegistryEntry:
    """A registered plugin entry."""
    manifest: PluginManifest
    plugin_path: str  # filesystem path to the plugin
    loaded: bool = False
    instance: Any = None  # the loaded TechnicalIndicator instance


class PluginRegistry:
    """Keeps track of every installed indicator plugin.

    Usage:
        registry = PluginRegistry()
        registry.register(manifest, path="/plugins/ema")
        entry = registry.get("ema")
        all_plugins = registry.list_all()
    """

    def __init__(self):
        self._entries: dict[str, RegistryEntry] = {}
        self._lock = RLock()

    def register(self, manifest: PluginManifest, plugin_path: str = "") -> None:
        """Register a plugin manifest."""
        with self._lock:
            if manifest.id in self._entries:
                log.warning("plugin_already_registered", plugin_id=manifest.id)
                return
            self._entries[manifest.id] = RegistryEntry(
                manifest=manifest,
                plugin_path=plugin_path,
            )
            log.info("plugin_registered",
                     plugin_id=manifest.id,
                     version=manifest.version,
                     category=manifest.category.value)

    def unregister(self, plugin_id: str) -> None:
        """Remove a plugin from the registry."""
        with self._lock:
            self._entries.pop(plugin_id, None)
            log.info("plugin_unregistered", plugin_id=plugin_id)

    def get(self, plugin_id: str) -> RegistryEntry | None:
        with self._lock:
            return self._entries.get(plugin_id)

    def list_all(self) -> list[RegistryEntry]:
        with self._lock:
            return list(self._entries.values())

    def list_enabled(self) -> list[RegistryEntry]:
        with self._lock:
            return [e for e in self._entries.values() if e.manifest.enabled]

    def list_by_category(self, category: PluginCategory) -> list[RegistryEntry]:
        with self._lock:
            return [e for e in self._entries.values() if e.manifest.category == category]

    def list_by_layer(self, layer: str) -> list[RegistryEntry]:
        with self._lock:
            return [e for e in self._entries.values() if e.manifest.layer.value == layer]

    def set_loaded(self, plugin_id: str, instance: Any) -> None:
        """Mark a plugin as loaded with its instance."""
        with self._lock:
            entry = self._entries.get(plugin_id)
            if entry:
                entry.loaded = True
                entry.instance = instance

    def set_enabled(self, plugin_id: str, enabled: bool) -> None:
        """Enable/disable a plugin at runtime."""
        with self._lock:
            entry = self._entries.get(plugin_id)
            if entry:
                # Manifests are frozen, so we create a new one
                old = entry.manifest
                new_manifest = PluginManifest(
                    id=old.id, name=old.name, version=old.version,
                    category=old.category, layer=old.layer,
                    timeframes=old.timeframes, inputs=old.inputs,
                    outputs=old.outputs, dependencies=old.dependencies,
                    refresh_interval_seconds=old.refresh_interval_seconds,
                    enabled=enabled, description=old.description,
                    author=old.author, config=old.config,
                )
                entry.manifest = new_manifest
                log.info("plugin_enabled_changed",
                         plugin_id=plugin_id, enabled=enabled)

    def count(self) -> int:
        with self._lock:
            return len(self._entries)

    def count_enabled(self) -> int:
        with self._lock:
            return sum(1 for e in self._entries.values() if e.manifest.enabled)

    def get_categories(self) -> list[PluginCategory]:
        """List all categories that have registered plugins."""
        with self._lock:
            return list(set(e.manifest.category for e in self._entries.values()))
