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
        "id: ema\nname: EMA\nversion: 1.0.0\ncategory: trend\nlayer: 2\n"
        "timeframes: [15M]\ninputs: [OHLCV]\noutputs: [ema20]\n"
        "dependencies: []\nenabled: true\n"
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
