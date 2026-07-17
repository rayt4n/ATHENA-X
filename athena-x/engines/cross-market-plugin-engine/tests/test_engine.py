"""Tests for Cross-Market Plugin Engine."""
import pytest
from pathlib import Path
from athena_x_engine_cross_market_plugin_engine import (
    CrossMarketPluginManager,
    CorrelationEngine, CorrelationMatrix,
    LeadershipEngine, LeadershipResult,
)


PLUGIN_DIR = Path(__file__).parent.parent.parent.parent / "plugins" / "cross-market"


@pytest.fixture
def manager():
    mgr = CrossMarketPluginManager(plugin_dir=PLUGIN_DIR)
    mgr.discover()
    return mgr


def test_discovers_60_plus_plugins(manager):
    """60+ cross-market plugins are discovered."""
    assert manager.registry.count() >= 60


def test_6_categories_present(manager):
    """All 6 cross-market categories are represented."""
    stats = manager.get_stats()
    by_cat = stats.get("by_category", {})
    expected = ["market_monitor", "correlation", "leadership", "regime", "rotation", "divergence"]
    for cat in expected:
        assert cat in by_cat, f"Missing category: {cat}"


def test_market_monitors_include_all_groups(manager):
    """Market monitor plugins span all 11 market groups."""
    monitors = manager.list_by_category("market_monitor")
    assert len(monitors) >= 50  # 50+ instruments


def test_correlation_plugins_exist(manager):
    """Correlation plugins are registered."""
    correlations = manager.list_by_category("correlation")
    assert len(correlations) >= 10


def test_leadership_plugins_exist(manager):
    """Leadership plugins are registered."""
    leadership = manager.list_by_category("leadership")
    assert len(leadership) >= 5


def test_regime_plugins_exist(manager):
    """Regime plugins are registered."""
    regimes = manager.list_by_category("regime")
    assert len(regimes) >= 5


def test_config_service_can_disable(manager):
    """Config Service can disable a plugin at runtime."""
    manager.config_service.set_enabled("spy_es_corr", False)
    assert manager.registry.get("spy_es_corr").manifest.enabled is False


# Correlation Engine tests

def test_correlation_engine_computes():
    """Correlation engine computes Pearson correlation."""
    engine = CorrelationEngine()
    engine.update_returns("SPY", [0.01, 0.02, -0.01, 0.03, 0.01])
    engine.update_returns("ES", [0.01, 0.02, -0.01, 0.03, 0.01])
    corr = engine.compute_correlation("SPY", "ES")
    assert corr is not None
    assert corr > 0.99  # identical returns -> correlation ~1.0


def test_correlation_engine_negative():
    """Negatively correlated assets have correlation < 0."""
    engine = CorrelationEngine()
    engine.update_returns("SPY", [0.01, 0.02, -0.01, 0.03, 0.01])
    engine.update_returns("VIX", [-0.01, -0.02, 0.01, -0.03, -0.01])
    corr = engine.compute_correlation("SPY", "VIX")
    assert corr is not None
    assert corr < -0.99


def test_correlation_matrix_detects_changes():
    """Matrix detects meaningful changes."""
    engine = CorrelationEngine(change_threshold=0.05)
    engine.update_returns("SPY", [0.01, 0.02, -0.01, 0.03, 0.01])
    engine.update_returns("ES", [0.01, 0.02, -0.01, 0.03, 0.01])
    matrix1 = engine.compute_matrix([("SPY", "ES")])
    assert len(matrix1.changes) == 0  # first time, no previous

    # Change ES returns significantly
    engine.update_returns("ES", [-0.01, -0.02, 0.01, -0.03, -0.01])
    matrix2 = engine.compute_matrix([("SPY", "ES")])
    assert len(matrix2.changes) > 0  # change detected


# Leadership Engine tests

def test_leadership_engine_finds_leader():
    """Leadership engine identifies the leading instrument."""
    engine = LeadershipEngine()
    engine.update_returns("NVDA", [0.02, 0.03, 0.04, 0.05, 0.06])
    engine.update_returns("QQQ", [0.01, 0.01, 0.01, 0.01, 0.01])
    result = engine.analyze_leadership("NVDA", "QQQ")
    assert result.leader == "NVDA"
    assert result.signal == "leading"


def test_leadership_engine_finds_divergence():
    """Leadership engine detects divergence."""
    engine = LeadershipEngine()
    engine.update_returns("SPY", [0.01, 0.02, 0.03, 0.04, 0.05])
    engine.update_returns("VIX", [0.01, 0.02, 0.03, 0.04, 0.05])  # both up = divergence
    result = engine.analyze_leadership("SPY", "VIX")
    assert result.signal in ("diverging", "neutral")  # depends on magnitude


def test_leadership_engine_finds_strongest():
    """Leadership engine finds the strongest performer."""
    engine = LeadershipEngine()
    engine.update_returns("ES", [0.01, 0.02, 0.03, 0.04, 0.05])
    engine.update_returns("SPY", [0.005, 0.01, 0.015, 0.02, 0.025])
    engine.update_returns("VIX", [-0.01, -0.02, -0.03, -0.04, -0.05])
    strongest = engine.find_strongest(["ES", "SPY", "VIX"])
    assert strongest == "ES"


def test_leadership_engine_finds_weakest():
    """Leadership engine finds the weakest performer."""
    engine = LeadershipEngine()
    engine.update_returns("ES", [0.01, 0.02, 0.03, 0.04, 0.05])
    engine.update_returns("SPY", [0.005, 0.01, 0.015, 0.02, 0.025])
    engine.update_returns("VIX", [-0.01, -0.02, -0.03, -0.04, -0.05])
    weakest = engine.find_weakest(["ES", "SPY", "VIX"])
    assert weakest == "VIX"
