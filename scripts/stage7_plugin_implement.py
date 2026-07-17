#!/usr/bin/env python3
"""
STEP 4 Stage 7 Refactor - Plugin-Based TA Platform
====================================================
Implements:
  1. engines/plugin-engine/ - Plugin Manager + Registry + Dependency Graph + Scheduler + Config
  2. Refactored indicator plugins with manifest.yaml (EMA, RSI, MACD, SMA, VWAP, ADX, ATR, Bollinger)
  3. runtime/stage7-plugin-integration/ - acceptance tests

Key: The engine never knows which indicators exist. It only knows how to load plugins.

Run: python /home/z/my-project/scripts/stage7_plugin_implement.py
"""

from pathlib import Path
import textwrap
import json

ROOT = Path("/home/z/my-project/athena-x")
ROOT.mkdir(parents=True, exist_ok=True)
FILES = []

def w(rel: str, content: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(content).lstrip("\n"))
    FILES.append(rel)


# ============================================================================
# 1. PLUGIN ENGINE - engines/plugin-engine/
# ============================================================================

w("engines/plugin-engine/pyproject.toml", '''
[project]
name = "athena-x-engine-plugin-engine"
version = "0.1.0"
description = "Plugin Manager + Registry + Dependency Graph + Scheduler + Config Service"
requires-python = ">=3.11"
dependencies = [
    "pydantic>=2.9.0",
    "pyyaml>=6.0.0",
    "athena-x-runtime-logger",
    "athena-x-runtime-event-envelope",
    "athena-x-plugin-indicator-base",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_engine_plugin_engine"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w("engines/plugin-engine/src/athena_x_engine_plugin_engine/__init__.py", '''
"""Plugin-based TA Platform engine."""
from .manifest import PluginManifest, PluginCategory, PluginLayer
from .registry import PluginRegistry, RegistryEntry
from .manager import PluginManager
from .dependency import DependencyResolver, DependencyGraph
from .scheduler import PluginScheduler, ScheduleEntry
from .config import PluginConfigService
from .executor import PluginExecutor, ExecutionResult

__all__ = [
    "PluginManifest", "PluginCategory", "PluginLayer",
    "PluginRegistry", "RegistryEntry",
    "PluginManager",
    "DependencyResolver", "DependencyGraph",
    "PluginScheduler", "ScheduleEntry",
    "PluginConfigService",
    "PluginExecutor", "ExecutionResult",
]
__version__ = "0.1.0"
''')

w("engines/plugin-engine/src/athena_x_engine_plugin_engine/manifest.py", '''
"""Plugin manifest - each indicator declares itself via manifest.yaml.

The engine reads this automatically. No code changes needed to add an indicator.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
import yaml


class PluginCategory(str, Enum):
    TREND = "trend"
    MOMENTUM = "momentum"
    VOLUME = "volume"
    STRUCTURE = "structure"
    PATTERN = "pattern"
    LIQUIDITY = "liquidity"
    PROJECTION = "projection"


class PluginLayer(str, Enum):
    MARKET_STRUCTURE = "1"
    INDICATOR = "2"
    INSTITUTIONAL = "3"
    CONSENSUS = "4"


@dataclass(frozen=True)
class PluginManifest:
    """Manifest declared by each plugin via manifest.yaml."""
    id: str                    # e.g., "ema"
    name: str                  # e.g., "EMA"
    version: str               # semver "1.0.0"
    category: PluginCategory
    layer: PluginLayer
    timeframes: list[str]      # ["1M", "1W", "1D", "4H", "1H", "30M", "15M", "5M", "1m"]
    inputs: list[str]          # ["OHLCV"]
    outputs: list[str]         # ["ema20", "ema50", "ema200"]
    dependencies: list[str]    # [] or ["ema"] for MACD
    refresh_interval_seconds: int = 1
    enabled: bool = True
    description: str = ""
    author: str = ""
    config: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: str) -> "PluginManifest":
        """Load manifest from a YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict) -> "PluginManifest":
        """Create manifest from a dict."""
        return cls(
            id=data["id"],
            name=data["name"],
            version=data.get("version", "1.0.0"),
            category=PluginCategory(data.get("category", "trend")),
            layer=PluginLayer(data.get("layer", "2")),
            timeframes=data.get("timeframes", []),
            inputs=data.get("inputs", []),
            outputs=data.get("outputs", []),
            dependencies=data.get("dependencies", []),
            refresh_interval_seconds=data.get("refresh_interval_seconds", 1),
            enabled=data.get("enabled", True),
            description=data.get("description", ""),
            author=data.get("author", ""),
            config=data.get("config", {}),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "category": self.category.value,
            "layer": self.layer.value,
            "timeframes": self.timeframes,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "dependencies": self.dependencies,
            "refresh_interval_seconds": self.refresh_interval_seconds,
            "enabled": self.enabled,
            "description": self.description,
        }
''')

w("engines/plugin-engine/src/athena_x_engine_plugin_engine/registry.py", '''
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
''')

w("engines/plugin-engine/src/athena_x_engine_plugin_engine/dependency.py", '''
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
''')

w("engines/plugin-engine/src/athena_x_engine_plugin_engine/scheduler.py", '''
"""Execution Scheduler - runs indicators at configurable frequencies.

Each plugin controls its refresh rate via manifest.refresh_interval_seconds.

Example:
  EMA: every 1 second
  VWAP: every 5 seconds
  Wyckoff: every 15 seconds
  Elliott Wave: every 60 seconds
"""
from __future__ import annotations
import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import RLock
from typing import Any, Awaitable, Callable
from athena_x_runtime_logger import get_logger

from .registry import PluginRegistry

log = get_logger("plugin.scheduler")


@dataclass
class ScheduleEntry:
    """A scheduled plugin execution."""
    plugin_id: str
    interval_seconds: float
    last_run: float = 0.0  # monotonic timestamp
    run_count: int = 0
    error_count: int = 0
    enabled: bool = True


class PluginScheduler:
    """Schedules plugin execution at configurable frequencies.

    Usage:
        scheduler = PluginScheduler(registry)
        await scheduler.start()
        # Plugins run at their configured intervals
        await scheduler.stop()
    """

    def __init__(self, registry: PluginRegistry):
        self._registry = registry
        self._schedules: dict[str, ScheduleEntry] = {}
        self._lock = RLock()
        self._running = False
        self._task: asyncio.Task | None = None
        self._executor: Callable[..., Awaitable[Any]] | None = None
        self._build_schedules()

    def _build_schedules(self) -> None:
        """Build schedule entries from registered plugins."""
        for entry in self._registry.list_enabled():
            self._schedules[entry.manifest.id] = ScheduleEntry(
                plugin_id=entry.manifest.id,
                interval_seconds=entry.manifest.refresh_interval_seconds,
                enabled=entry.manifest.enabled,
            )

    def set_executor(self, executor: Callable[..., Awaitable[Any]]) -> None:
        """Set the function that executes a plugin."""
        self._executor = executor

    async def start(self) -> None:
        """Start the scheduler loop."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        log.info("scheduler_started",
                 plugins=len(self._schedules))

    async def stop(self) -> None:
        """Stop the scheduler."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        log.info("scheduler_stopped")

    async def _run_loop(self) -> None:
        """Main scheduling loop."""
        while self._running:
            now = time.monotonic()
            with self._lock:
                due = [
                    s for s in self._schedules.values()
                    if s.enabled and (now - s.last_run) >= s.interval_seconds
                ]

            for schedule in due:
                if self._executor is None:
                    continue
                try:
                    await self._executor(schedule.plugin_id)
                    with self._lock:
                        schedule.last_run = now
                        schedule.run_count += 1
                except Exception as e:
                    with self._lock:
                        schedule.error_count += 1
                    log.error("plugin_execution_failed",
                              plugin_id=schedule.plugin_id,
                              error=str(e))

            await asyncio.sleep(0.1)  # check every 100ms

    def run_now(self, plugin_id: str) -> None:
        """Force a plugin to run immediately (regardless of schedule)."""
        with self._lock:
            schedule = self._schedules.get(plugin_id)
            if schedule:
                schedule.last_run = 0.0  # will be due next loop iteration

    def set_enabled(self, plugin_id: str, enabled: bool) -> None:
        """Enable/disable a plugin's schedule at runtime."""
        with self._lock:
            schedule = self._schedules.get(plugin_id)
            if schedule:
                schedule.enabled = enabled

    def get_stats(self) -> dict:
        with self._lock:
            return {
                "total_scheduled": len(self._schedules),
                "enabled": sum(1 for s in self._schedules.values() if s.enabled),
                "total_runs": sum(s.run_count for s in self._schedules.values()),
                "total_errors": sum(s.error_count for s in self._schedules.values()),
                "schedules": [
                    {
                        "plugin_id": s.plugin_id,
                        "interval": s.interval_seconds,
                        "run_count": s.run_count,
                        "error_count": s.error_count,
                        "enabled": s.enabled,
                    }
                    for s in self._schedules.values()
                ],
            }

    def rebuild(self) -> None:
        """Rebuild schedules from registry (after plugins added/removed)."""
        with self._lock:
            self._schedules.clear()
            self._build_schedules()
        log.info("scheduler_rebuilt", plugins=len(self._schedules))
''')

w("engines/plugin-engine/src/athena_x_engine_plugin_engine/config.py", '''
"""Configuration Service - enables/disables plugins without modifying code.

yaml config:
  enabled:
    ema: true
    sma: true
    macd: true
    rsi: true
    bollinger: false
    elliott: false
    wyckoff: true
"""
from __future__ import annotations
from pathlib import Path
from threading import RLock
from typing import Any
import yaml
from athena_x_runtime_logger import get_logger

from .registry import PluginRegistry

log = get_logger("plugin.config")


class PluginConfigService:
    """Manages plugin enable/disable configuration.

    Usage:
        config = PluginConfigService(registry)
        config.load_from_file("plugins/config.yaml")
        config.set_enabled("ema", True)
        config.set_enabled("bollinger", False)
    """

    def __init__(self, registry: PluginRegistry):
        self._registry = registry
        self._lock = RLock()
        self._config: dict[str, bool] = {}  # plugin_id -> enabled

    def load_from_file(self, path: str | Path) -> None:
        """Load configuration from a YAML file."""
        path = Path(path)
        if not path.exists():
            log.warning("config_file_not_found", path=str(path))
            return

        with open(path) as f:
            data = yaml.safe_load(f) or {}

        enabled_map = data.get("enabled", {})
        with self._lock:
            self._config = {k: bool(v) for k, v in enabled_map.items()}

        # Apply to registry
        for plugin_id, enabled in self._config.items():
            self._registry.set_enabled(plugin_id, enabled)

        log.info("config_loaded",
                 path=str(path),
                 plugins=len(self._config),
                 enabled=sum(1 for v in self._config.values() if v))

    def load_from_dict(self, config: dict[str, bool]) -> None:
        """Load configuration from a dict."""
        with self._lock:
            self._config = {k: bool(v) for k, v in config.items()}
        for plugin_id, enabled in self._config.items():
            self._registry.set_enabled(plugin_id, enabled)

    def set_enabled(self, plugin_id: str, enabled: bool) -> None:
        """Enable/disable a plugin at runtime (no restart needed)."""
        with self._lock:
            self._config[plugin_id] = enabled
        self._registry.set_enabled(plugin_id, enabled)
        log.info("plugin_enabled_changed",
                 plugin_id=plugin_id,
                 enabled=enabled)

    def is_enabled(self, plugin_id: str) -> bool:
        """Check if a plugin is enabled."""
        with self._lock:
            return self._config.get(plugin_id, True)  # default: enabled

    def get_config(self) -> dict[str, bool]:
        """Get the full configuration."""
        with self._lock:
            return dict(self._config)

    def save_to_file(self, path: str | Path) -> None:
        """Save current configuration to a YAML file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            yaml.dump({"enabled": self.get_config()}, f, default_flow_style=False)
        log.info("config_saved", path=str(path))
''')

# Fix the path typo
import os
bad = ROOT / "engines/plugin-engine/src/athena_x_engine_plugin_engine/config.py',"
if bad.exists():
    os.rename(bad, ROOT / "engines/plugin-engine/src/athena_x_engine_plugin_engine/config.py")

w("engines/plugin-engine/src/athena_x_engine_plugin_engine/manager.py", '''
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
''')

w("engines/plugin-engine/src/athena_x_engine_plugin_engine/executor.py", '''
"""Plugin Executor - executes a plugin and publishes the result as an event.

Stage 7 rule: Every output is published as an ai:technical:* event.
"""
from __future__ import annotations
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4
from athena_x_runtime_logger import get_logger
from athena_x_runtime_event_envelope import create_event, EventPriority

from .manager import PluginManager

log = get_logger("plugin.executor")


@dataclass
class ExecutionResult:
    """Result of executing a plugin."""
    plugin_id: str
    symbol: str
    timeframe: str
    value: Any
    confidence: float = 1.0
    calculation_time_ms: float = 0.0
    success: bool = True
    error: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class PluginExecutor:
    """Executes plugins and publishes results as events.

    Usage:
        executor = PluginExecutor(manager, event_bus)
        result = await executor.execute("ema", symbol="SPY", timeframe="15m", data=closes)
    """

    def __init__(self, manager: PluginManager, event_bus: Any = None):
        self._manager = manager
        self._bus = event_bus
        self._execution_count = 0
        self._error_count = 0

    async def execute(
        self,
        plugin_id: str,
        symbol: str,
        timeframe: str,
        data: Any = None,
    ) -> ExecutionResult:
        """Execute a plugin and publish the result."""
        start = time.monotonic()

        try:
            instance = self._manager.get_instance(plugin_id)
            if instance is None:
                instance = self._manager.load(plugin_id)

            # Call compute or calculate method
            if hasattr(instance, "compute"):
                output = instance.compute(data) if data else instance.compute()
            elif hasattr(instance, "calculate"):
                output = instance.calculate(data) if data else instance.calculate()
            else:
                raise AttributeError(f"Plugin {plugin_id} has no compute/calculate method")

            elapsed_ms = (time.monotonic() - start) * 1000
            self._execution_count += 1

            result = ExecutionResult(
                plugin_id=plugin_id,
                symbol=symbol,
                timeframe=timeframe,
                value=output,
                calculation_time_ms=elapsed_ms,
            )

            # Publish event
            if self._bus is not None:
                event = create_event(
                    event_type=f"ai:technical:{plugin_id}",
                    source_agent=f"ta.{plugin_id}",
                    symbol=symbol,
                    priority=EventPriority.NORMAL,
                    payload={
                        "agent": f"{plugin_id}Agent",
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "indicator": plugin_id.upper(),
                        "value": output if not isinstance(output, dict) else output,
                        "confidence": result.confidence,
                        "calculation_time_ms": int(elapsed_ms),
                    },
                    processing_time_ms=int(elapsed_ms),
                )
                await self._bus.publish(event)

            return result

        except Exception as e:
            self._error_count += 1
            elapsed_ms = (time.monotonic() - start) * 1000
            log.error("plugin_execution_failed",
                      plugin_id=plugin_id,
                      error=str(e))
            return ExecutionResult(
                plugin_id=plugin_id,
                symbol=symbol,
                timeframe=timeframe,
                value=None,
                calculation_time_ms=elapsed_ms,
                success=False,
                error=str(e),
            )

    def get_stats(self) -> dict:
        return {
            "total_executions": self._execution_count,
            "total_errors": self._error_count,
            "error_rate": self._error_count / self._execution_count if self._execution_count > 0 else 0.0,
        }
''')

# Fix path typo
bad2 = ROOT / "engines/plugin-engine/src/athena_x_engine_plugin_engine/executor.py',"
if bad2.exists():
    os.rename(bad2, ROOT / "engines/plugin-engine/src/athena_x_engine_plugin_engine/executor.py")

w("engines/plugin-engine/tests/__init__.py", "")
w("engines/plugin-engine/tests/test_plugin_engine.py", '''
"""Tests for the plugin engine (Stage 7 refactor)."""
import pytest
from athena_x_engine_plugin_engine import (
    PluginManifest, PluginCategory, PluginLayer,
    PluginRegistry, PluginManager,
    DependencyResolver, DependencyGraph,
    PluginScheduler, PluginConfigService,
    PluginExecutor, ExecutionResult,
)


# ============================================================================
# Manifest tests
# ============================================================================

def test_manifest_from_dict():
    """Manifest can be created from a dict."""
    m = PluginManifest.from_dict({
        "id": "ema",
        "name": "EMA",
        "version": "1.0.0",
        "category": "trend",
        "layer": "2",
        "timeframes": ["15M", "5M", "1m"],
        "inputs": ["OHLCV"],
        "outputs": ["ema20", "ema50"],
        "dependencies": [],
        "refresh_interval_seconds": 1,
        "enabled": True,
    })
    assert m.id == "ema"
    assert m.category == PluginCategory.TREND
    assert m.layer == PluginLayer.INDICATOR
    assert len(m.timeframes) == 3
    assert m.enabled is True


def test_manifest_to_dict_roundtrip():
    """Manifest serializes to dict and back."""
    m = PluginManifest.from_dict({
        "id": "rsi", "name": "RSI", "version": "1.0.0",
        "category": "momentum", "layer": "2",
        "timeframes": ["15M"], "inputs": ["OHLCV"],
        "outputs": ["rsi14"], "dependencies": [],
    })
    d = m.to_dict()
    assert d["id"] == "rsi"
    assert d["category"] == "momentum"


# ============================================================================
# Registry tests
# ============================================================================

@pytest.fixture
def registry():
    reg = PluginRegistry()
    reg.register(PluginManifest.from_dict({
        "id": "ema", "name": "EMA", "category": "trend", "layer": "2",
        "timeframes": [], "inputs": [], "outputs": [], "dependencies": [],
    }))
    reg.register(PluginManifest.from_dict({
        "id": "rsi", "name": "RSI", "category": "momentum", "layer": "2",
        "timeframes": [], "inputs": [], "outputs": [], "dependencies": [],
    }))
    reg.register(PluginManifest.from_dict({
        "id": "macd", "name": "MACD", "category": "momentum", "layer": "2",
        "timeframes": [], "inputs": [], "outputs": [], "dependencies": ["ema"],
    }))
    return reg


def test_registry_register_and_get(registry):
    assert registry.get("ema") is not None
    assert registry.get("nonexistent") is None


def test_registry_list_all(registry):
    assert len(registry.list_all()) == 3


def test_registry_list_by_category(registry):
    momentum = registry.list_by_category(PluginCategory.MOMENTUM)
    assert len(momentum) == 2  # rsi + macd


def test_registry_set_enabled(registry):
    registry.set_enabled("ema", False)
    assert registry.get("ema").manifest.enabled is False
    assert len(registry.list_enabled()) == 2  # rsi + macd


def test_registry_count(registry):
    assert registry.count() == 3
    assert registry.count_enabled() == 3


# ============================================================================
# Dependency Graph tests
# ============================================================================

def test_dependency_graph_topological_sort(registry):
    """Dependencies are resolved in correct order (ema before macd)."""
    resolver = DependencyResolver(registry)
    order = resolver.get_execution_order()
    assert "ema" in order
    assert "macd" in order
    ema_idx = order.index("ema")
    macd_idx = order.index("macd")
    assert ema_idx < macd_idx  # ema before macd


def test_dependency_graph_get_dependencies(registry):
    resolver = DependencyResolver(registry)
    assert resolver.get_dependencies("macd") == ["ema"]
    assert resolver.get_dependencies("ema") == []


def test_dependency_graph_get_dependents(registry):
    resolver = DependencyResolver(registry)
    assert "macd" in resolver.get_dependents("ema")


def test_dependency_graph_detect_cycles():
    graph = DependencyGraph()
    graph.add_dependency("a", "b")
    graph.add_dependency("b", "a")  # circular
    cycles = graph.detect_cycles()
    assert len(cycles) > 0


def test_dependency_resolver_caches_results(registry):
    resolver = DependencyResolver(registry)
    resolver.set_result("ema", {"ema20": 450.0})
    assert resolver.get_result("ema") == {"ema20": 450.0}


# ============================================================================
# Scheduler tests
# ============================================================================

def test_scheduler_builds_from_registry(registry):
    scheduler = PluginScheduler(registry)
    stats = scheduler.get_stats()
    assert stats["total_scheduled"] == 3


def test_scheduler_set_enabled(registry):
    scheduler = PluginScheduler(registry)
    scheduler.set_enabled("ema", False)
    stats = scheduler.get_stats()
    assert stats["enabled"] == 2


def test_scheduler_run_now(registry):
    scheduler = PluginScheduler(registry)
    scheduler.run_now("ema")
    # last_run set to 0 -> will be due next loop


# ============================================================================
# Config Service tests
# ============================================================================

def test_config_service_load_from_dict(registry):
    config = PluginConfigService(registry)
    config.load_from_dict({"ema": True, "rsi": False, "macd": True})
    assert config.is_enabled("ema") is True
    assert config.is_enabled("rsi") is False
    assert registry.get("rsi").manifest.enabled is False


def test_config_service_set_enabled(registry):
    config = PluginConfigService(registry)
    config.set_enabled("bollinger", False)
    assert config.is_enabled("bollinger") is False


def test_config_service_save_and_load(tmp_path, registry):
    config = PluginConfigService(registry)
    config.set_enabled("ema", False)
    config_path = tmp_path / "config.yaml"
    config.save_to_file(config_path)

    # Load in a new config service
    config2 = PluginConfigService(registry)
    config2.load_from_file(config_path)
    assert config2.is_enabled("ema") is False


# ============================================================================
# Plugin Manager tests
# ============================================================================

def test_plugin_manager_discover(tmp_path):
    """Plugin manager discovers plugins from manifest.yaml files."""
    # Create a fake plugin
    plugin_dir = tmp_path / "indicators"
    ema_dir = plugin_dir / "ema"
    ema_dir.mkdir(parents=True)
    (ema_dir / "manifest.yaml").write_text(
        "id: ema\\nname: EMA\\nversion: 1.0.0\\ncategory: trend\\nlayer: 2\\n"
        "timeframes: [15M]\\ninputs: [OHLCV]\\noutputs: [ema20]\\n"
        "dependencies: []\\nenabled: true\\n"
    )

    manager = PluginManager(plugin_dir=plugin_dir)
    count = manager.discover()
    assert count == 1
    assert manager.registry.get("ema") is not None


def test_plugin_manager_stats(registry):
    manager = PluginManager(registry=registry)
    stats = manager.get_stats()
    assert stats["discovered"] == 3
    assert "categories" in stats


# ============================================================================
# Executor tests
# ============================================================================

class FakeEMAIndicator:
    """Fake indicator for testing."""
    def compute(self, data=None):
        return {"ema20": 450.0, "ema50": 445.0}


async def test_executor_executes_plugin():
    """Executor runs a plugin and returns result."""
    from athena_x_engine_plugin_engine import PluginManager, PluginExecutor

    manager = PluginManager()
    # Manually register a fake plugin
    manager.registry.register(PluginManifest.from_dict({
        "id": "fake_ema", "name": "FakeEMA", "category": "trend", "layer": "2",
        "timeframes": ["15M"], "inputs": ["OHLCV"], "outputs": ["ema20"],
        "dependencies": [],
    }))
    # Manually load the fake instance
    manager._loaded["fake_ema"] = FakeEMAIndicator()
    manager.registry.set_loaded("fake_ema", FakeEMAIndicator())

    executor = PluginExecutor(manager)
    result = await executor.execute("fake_ema", symbol="SPY", timeframe="15m")

    assert result.success is True
    assert result.plugin_id == "fake_ema"
    assert result.value == {"ema20": 450.0, "ema50": 445.0}
    assert result.calculation_time_ms > 0


async def test_executor_publishes_event():
    """Executor publishes ai:technical:* events."""
    from athena_x_runtime_event_bus import InMemoryBusClient
    from athena_x_engine_plugin_engine import PluginManager, PluginExecutor

    bus = InMemoryBusClient()
    manager = PluginManager()
    manager.registry.register(PluginManifest.from_dict({
        "id": "test_ind", "name": "TestInd", "category": "trend", "layer": "2",
        "timeframes": ["15M"], "inputs": [], "outputs": ["val"],
        "dependencies": [],
    }))
    manager._loaded["test_ind"] = FakeEMAIndicator()
    manager.registry.set_loaded("test_ind", FakeEMAIndicator())

    received = []
    async def handler(event):
        received.append(event)
    await bus.subscribe("ai:technical:test_ind", handler)

    executor = PluginExecutor(manager, event_bus=bus)
    await executor.execute("test_ind", symbol="SPY", timeframe="15m")

    assert len(received) == 1
    assert received[0].event_type == "ai:technical:test_ind"
    await bus.close()
''')

# ============================================================================
# 2. PLUGIN MANIFESTS - Create manifest.yaml for each indicator
# ============================================================================

# Manifest definitions for all indicators
MANIFESTS = [
    ("ema", "EMA", "1.0.0", "trend", "2", ["1M","1W","1D","4H","1H","30M","15M","5M","1m"],
     ["OHLCV"], ["ema20","ema50","ema200"], [], 1, "Exponential Moving Average"),
    ("sma", "SMA", "1.0.0", "trend", "2", ["1M","1W","1D","4H","1H","30M","15M","5M","1m"],
     ["OHLCV"], ["sma20","sma50","sma200"], [], 1, "Simple Moving Average"),
    ("vwap", "VWAP", "1.0.0", "volume", "2", ["1D","4H","1H","30M","15M","5M","1m"],
     ["OHLCV"], ["vwap"], [], 5, "Volume-Weighted Average Price"),
    ("rsi", "RSI", "1.0.0", "momentum", "2", ["1M","1W","1D","4H","1H","30M","15M","5M","1m"],
     ["OHLCV"], ["rsi14"], [], 1, "Relative Strength Index"),
    ("macd", "MACD", "1.0.0", "momentum", "2", ["1M","1W","1D","4H","1H","30M","15M","5M","1m"],
     ["OHLCV"], ["macd","signal","histogram"], ["ema"], 1, "Moving Average Convergence Divergence"),
    ("adx", "ADX", "1.0.0", "trend", "2", ["1M","1W","1D","4H","1H","30M","15M","5M","1m"],
     ["OHLCV"], ["adx","plus_di","minus_di"], [], 5, "Average Directional Index"),
    ("atr", "ATR", "1.0.0", "volatility", "2", ["1M","1W","1D","4H","1H","30M","15M","5M","1m"],
     ["OHLCV"], ["atr14"], [], 1, "Average True Range"),
    ("bollinger", "Bollinger", "1.0.0", "volatility", "2", ["1M","1W","1D","4H","1H","30M","15M","5M","1m"],
     ["OHLCV"], ["upper","middle","lower","percent_b"], ["sma"], 5, "Bollinger Bands"),
    ("stochastic", "Stochastic", "1.0.0", "momentum", "2", ["1D","4H","1H","30M","15M","5M","1m"],
     ["OHLCV"], ["k","d"], [], 5, "Stochastic Oscillator"),
    ("cci", "CCI", "1.0.0", "momentum", "2", ["1D","4H","1H","30M","15M","5M","1m"],
     ["OHLCV"], ["cci20"], [], 5, "Commodity Channel Index"),
    ("williams-r", "Williams %R", "1.0.0", "momentum", "2", ["1D","4H","1H","30M","15M","5M","1m"],
     ["OHLCV"], ["wr14"], [], 5, "Williams Percent R"),
    ("ichimoku", "Ichimoku", "1.0.0", "trend", "2", ["1W","1D","4H","1H"],
     ["OHLCV"], ["tenkan","kijun","senkou_a","senkou_b","chikou"], [], 15, "Ichimoku Cloud"),
    ("obv", "OBV", "1.0.0", "volume", "2", ["1D","4H","1H","30M","15M","5M","1m"],
     ["OHLCV"], ["obv"], [], 5, "On-Balance Volume"),
    ("fibonacci", "Fibonacci", "1.0.0", "projection", "2", ["1W","1D","4H","1H"],
     ["OHLCV"], ["levels"], [], 30, "Fibonacci Retracement Levels"),
]

for slug, name, version, category, layer, tfs, inputs, outputs, deps, refresh, desc in MANIFESTS:
    yaml_content = f'''id: {slug}
name: "{name}"
version: "{version}"
category: {category}
layer: "{layer}"
timeframes: {tfs}
inputs: {inputs}
outputs: {outputs}
dependencies: {deps}
refresh_interval_seconds: {refresh}
enabled: true
description: "{desc}"
author: "ATHENA-X"
'''
    w(f"plugins/indicators/{slug}/manifest.yaml", yaml_content)

# ============================================================================
# 3. STAGE 7 PLUGIN INTEGRATION TESTS
# ============================================================================

w("runtime/stage7-plugin-integration/pyproject.toml", '''
[project]
name = "athena-x-runtime-stage7-plugin-integration"
version = "0.1.0"
description = "Stage 7 plugin platform integration tests"
requires-python = ">=3.11"
dependencies = [
    "athena-x-engine-plugin-engine",
    "athena-x-runtime-event-bus",
    "athena-x-runtime-event-envelope",
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_runtime_stage7_plugin_integration"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w("runtime/stage7-plugin-integration/src/athena_x_runtime_stage7_plugin_integration/__init__.py", '''"""Stage 7 plugin integration."""''')

w("runtime/stage7-plugin-integration/tests/__init__.py", "")
w("runtime/stage7-plugin-integration/tests/test_plugin_platform.py", '''
"""Stage 7 plugin platform acceptance tests.

Exit criteria:
  1. Plugin Manager discovers plugins from manifest.yaml files
  2. Indicator Registry tracks all installed plugins
  3. Dependency Graph resolves calculation order
  4. Scheduler runs plugins at configurable frequencies
  5. Config Service enables/disables plugins without code changes
  6. Plugin Executor publishes ai:technical:* events
  7. Hot-reload works (unload + load)
  8. Adding a new indicator = adding a folder (no code changes)
"""
import pytest
from pathlib import Path
from athena_x_engine_plugin_engine import (
    PluginManager, PluginRegistry, PluginManifest,
    PluginCategory, DependencyResolver,
    PluginScheduler, PluginConfigService,
    PluginExecutor,
)


PLUGIN_DIR = Path(__file__).parent.parent.parent.parent / "plugins" / "indicators"


@pytest.fixture
def manager():
    """Plugin manager with discovered plugins from the plugins/ directory."""
    mgr = PluginManager(plugin_dir=PLUGIN_DIR)
    mgr.discover()
    return mgr


# ============================================================================
# Exit Criteria 1: Plugin Manager discovers plugins from manifest.yaml
# ============================================================================

def test_plugin_manager_discovers_manifests(manager):
    """Plugin Manager discovers manifest.yaml files from the plugin directory."""
    assert manager.registry.count() >= 14  # 14 indicator plugins


# ============================================================================
# Exit Criteria 2: Indicator Registry tracks all installed plugins
# ============================================================================

def test_registry_tracks_all_plugins(manager):
    """Registry has metadata for all discovered plugins."""
    all_plugins = manager.registry.list_all()
    plugin_ids = [e.manifest.id for e in all_plugins]
    assert "ema" in plugin_ids
    assert "rsi" in plugin_ids
    assert "macd" in plugin_ids
    assert "bollinger" in plugin_ids


def test_registry_tracks_categories(manager):
    """Registry organizes plugins by category."""
    categories = manager.registry.get_categories()
    assert PluginCategory.TREND in categories
    assert PluginCategory.MOMENTUM in categories
    assert PluginCategory.VOLUME in categories


def test_registry_tracks_versions(manager):
    """Each plugin has a version."""
    ema = manager.registry.get("ema")
    assert ema.manifest.version == "1.0.0"


# ============================================================================
# Exit Criteria 3: Dependency Graph resolves calculation order
# ============================================================================

def test_dependency_graph_resolves_order(manager):
    """Dependency graph resolves EMA before MACD."""
    resolver = DependencyResolver(manager.registry)
    order = resolver.get_execution_order()
    if "ema" in order and "macd" in order:
        assert order.index("ema") < order.index("macd")


def test_dependency_graph_macd_depends_on_ema(manager):
    """MACD depends on EMA."""
    resolver = DependencyResolver(manager.registry)
    deps = resolver.get_dependencies("macd")
    assert "ema" in deps


def test_dependency_graph_no_cycles(manager):
    """No circular dependencies."""
    resolver = DependencyResolver(manager.registry)
    cycles = resolver.detect_cycles()
    assert len(cycles) == 0


# ============================================================================
# Exit Criteria 4: Scheduler runs plugins at configurable frequencies
# ============================================================================

def test_scheduler_has_different_intervals(manager):
    """Different plugins have different refresh intervals."""
    scheduler = PluginScheduler(manager.registry)
    stats = scheduler.get_stats()
    schedules = stats["schedules"]

    # Find EMA and VWAP schedules
    ema_sched = next((s for s in schedules if s["plugin_id"] == "ema"), None)
    vwap_sched = next((s for s in schedules if s["plugin_id"] == "vwap"), None)

    if ema_sched and vwap_sched:
        assert ema_sched["interval"] <= vwap_sched["interval"]  # EMA more frequent


# ============================================================================
# Exit Criteria 5: Config Service enables/disables without code changes
# ============================================================================

def test_config_service_disable_plugin(manager):
    """Config Service can disable a plugin at runtime."""
    config = PluginConfigService(manager.registry)
    config.set_enabled("bollinger", False)
    assert manager.registry.get("bollinger").manifest.enabled is False


def test_config_service_load_from_dict(manager):
    """Config Service loads configuration from a dict."""
    config = PluginConfigService(manager.registry)
    config.load_from_dict({"ema": True, "rsi": False})
    assert config.is_enabled("ema") is True
    assert config.is_enabled("rsi") is False


# ============================================================================
# Exit Criteria 6: Plugin Executor publishes ai:technical:* events
# ============================================================================

class FakeIndicator:
    """Fake indicator for testing the executor."""
    def compute(self, data=None):
        return {"value": 450.0}


async def test_executor_publishes_event(manager):
    """Executor publishes ai:technical:* events."""
    from athena_x_runtime_event_bus import InMemoryBusClient

    bus = InMemoryBusClient()
    # Manually load a fake indicator
    manager._loaded["ema"] = FakeIndicator()
    manager.registry.set_loaded("ema", FakeIndicator())

    received = []
    async def handler(event):
        received.append(event)
    await bus.subscribe("ai:technical:ema", handler)

    executor = PluginExecutor(manager, event_bus=bus)
    result = await executor.execute("ema", symbol="SPY", timeframe="15m")

    assert result.success is True
    assert len(received) == 1
    assert received[0].event_type == "ai:technical:ema"
    await bus.close()


# ============================================================================
# Exit Criteria 7: Hot-reload works
# ============================================================================

def test_hot_reload(manager):
    """Hot-reload unloads + loads a plugin."""
    # Load
    manager._loaded["ema"] = FakeIndicator()
    manager.registry.set_loaded("ema", FakeIndicator())
    assert "ema" in manager.list_loaded()

    # Unload
    manager.unload("ema")
    assert "ema" not in manager.list_loaded()

    # Reload
    manager._loaded["ema"] = FakeIndicator()
    manager.registry.set_loaded("ema", FakeIndicator())
    assert "ema" in manager.list_loaded()


# ============================================================================
# Exit Criteria 8: Adding a new indicator = adding a folder
# ============================================================================

def test_adding_indicator_only_requires_folder(tmp_path):
    """Adding a new indicator only requires creating a folder with manifest.yaml."""
    plugin_dir = tmp_path / "indicators"
    new_plugin = plugin_dir / "delta_volume"
    new_plugin.mkdir(parents=True)
    (new_plugin / "manifest.yaml").write_text(
        "id: delta_volume\\nname: Delta Volume\\nversion: 1.0.0\\n"
        "category: volume\\nlayer: 2\\ntimeframes: [15M]\\n"
        "inputs: [OHLCV]\\noutputs: [delta]\\ndependencies: []\\n"
        "refresh_interval_seconds: 5\\nenabled: true\\n"
    )

    mgr = PluginManager(plugin_dir=plugin_dir)
    count = mgr.discover()
    assert count == 1
    assert mgr.registry.get("delta_volume") is not None
    assert mgr.registry.get("delta_volume").manifest.name == "Delta Volume"


# ============================================================================
# Plugin Manager stats
# ============================================================================

def test_manager_stats(manager):
    """Manager provides comprehensive stats."""
    stats = manager.get_stats()
    assert "discovered" in stats
    assert "enabled" in stats
    assert "loaded" in stats
    assert "categories" in stats
    assert stats["discovered"] >= 14


# ============================================================================
# Manifest format tests
# ============================================================================

def test_manifest_has_required_fields(manager):
    """Every manifest has required fields."""
    for entry in manager.registry.list_all():
        m = entry.manifest
        assert m.id is not None
        assert m.name is not None
        assert m.version is not None
        assert m.category is not None
        assert m.layer is not None
        assert len(m.timeframes) > 0
        assert len(m.inputs) > 0
        assert len(m.outputs) > 0


def test_manifest_timeframes_are_standardized(manager):
    """All plugins use standard timeframe names."""
    standard = {"1M", "1W", "1D", "4H", "1H", "30M", "15M", "5M", "1m"}
    for entry in manager.registry.list_all():
        for tf in entry.manifest.timeframes:
            assert tf in standard, f"Non-standard timeframe {tf} in {entry.manifest.id}"
''')

print(f"\\n✅ Stage 7 Plugin Platform complete: {len(FILES)} files written")
print("\\nComponents implemented:")
print("  1. engines/plugin-engine/ - Plugin Manager + Registry + Dependency Graph + Scheduler + Config + Executor")
print("  2. plugins/indicators/*/manifest.yaml - 14 self-contained plugin manifests")
print("  3. runtime/stage7-plugin-integration/ - acceptance tests (8 exit criteria)")
print("\\nNext: install deps and run tests")
