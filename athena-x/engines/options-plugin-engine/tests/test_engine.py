"""Tests for Options Plugin Engine."""
import pytest
from pathlib import Path
from athena_x_engine_options_plugin_engine import OptionsPluginManager


PLUGIN_DIR = Path(__file__).parent.parent.parent.parent / "plugins" / "options"


@pytest.fixture
def manager():
    mgr = OptionsPluginManager(plugin_dir=PLUGIN_DIR)
    mgr.discover()
    return mgr


def test_discovers_40_plus_plugins(manager):
    """Plugin manager discovers 40+ options plugins."""
    assert manager.registry.count() >= 40


def test_8_categories_present(manager):
    """All 8 options categories are represented."""
    stats = manager.get_stats()
    by_cat = stats.get("by_category", {})
    expected = ["volatility", "greeks", "dealer", "flow", "open_interest", "0dte", "dark_pool", "probability"]
    for cat in expected:
        assert cat in by_cat, f"Missing category: {cat}"


def test_dependency_graph_resolves_greeks_before_gex(manager):
    """GEX depends on gamma; gamma must come first."""
    resolver = manager.dependency_resolver
    deps = resolver.get_dependencies("gex")
    assert "gamma" in deps


def test_scheduler_has_different_intervals(manager):
    """Different plugins have different refresh intervals."""
    stats = manager.scheduler.get_stats()
    schedules = stats["schedules"]
    intervals = set(s["interval"] for s in schedules)
    assert len(intervals) > 1  # not all the same


def test_config_service_can_disable_plugin(manager):
    """Config service can disable a plugin at runtime."""
    manager.config_service.set_enabled("iv_crush_probability", False)
    assert manager.registry.get("iv_crush_probability").manifest.enabled is False


def test_0dte_plugins_exist(manager):
    """0DTE plugins are registered."""
    zero_dte = manager.list_by_category("0dte")
    assert len(zero_dte) >= 5  # at least 5 0DTE plugins


def test_all_manifests_have_required_fields(manager):
    """Every manifest has required fields."""
    for entry in manager.registry.list_all():
        m = entry.manifest
        assert m.id is not None
        assert m.name is not None
        assert m.version is not None
        assert len(m.outputs) > 0
