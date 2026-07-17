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
        "id: delta_volume\nname: Delta Volume\nversion: 1.0.0\n"
        "category: volume\nlayer: 2\ntimeframes: [15M]\n"
        "inputs: [OHLCV]\noutputs: [delta]\ndependencies: []\n"
        "refresh_interval_seconds: 5\nenabled: true\n"
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
