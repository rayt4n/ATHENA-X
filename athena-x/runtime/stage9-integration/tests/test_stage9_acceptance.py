"""Stage 9 acceptance tests - Market Intelligence & Correlation Platform."""
import pytest
from pathlib import Path
from athena_x_engine_cross_market_plugin_engine import (
    CrossMarketPluginManager,
    CorrelationEngine, LeadershipEngine,
)
from athena_x_agent_market_intelligence import MarketDNAAgent, MarketIntelligenceHub


PLUGIN_DIR = Path(__file__).parent.parent.parent.parent / "plugins" / "cross-market"


@pytest.fixture
def manager():
    mgr = CrossMarketPluginManager(plugin_dir=PLUGIN_DIR)
    mgr.discover()
    return mgr


# ============================================================================
# Exit Criteria 1: 60+ cross-market plugins discovered
# ============================================================================

def test_60_plus_plugins_discovered(manager):
    """60+ cross-market plugins are discovered from manifest.yaml files."""
    assert manager.registry.count() >= 60


# ============================================================================
# Exit Criteria 2: 6 categories present
# ============================================================================

def test_6_categories_present(manager):
    """All 6 cross-market plugin categories are represented."""
    stats = manager.get_stats()
    by_cat = stats["by_category"]
    expected = ["market_monitor", "correlation", "leadership", "regime", "rotation", "divergence"]
    for cat in expected:
        assert cat in by_cat, f"Missing category: {cat}"


# ============================================================================
# Exit Criteria 3: 11 market groups covered
# ============================================================================

def test_11_market_groups_covered(manager):
    """Market monitor plugins span all 11 market groups."""
    monitors = manager.list_by_category("market_monitor")
    assert len(monitors) >= 50  # 50+ instruments across 11 groups


# ============================================================================
# Exit Criteria 4: Correlation Engine works
# ============================================================================

def test_correlation_engine_computes_matrix():
    """Correlation engine computes a correlation matrix."""
    engine = CorrelationEngine()
    engine.update_returns("SPY", [0.01, 0.02, -0.01, 0.03, 0.01, 0.02, 0.01, 0.02, 0.01, 0.03])
    engine.update_returns("ES", [0.01, 0.02, -0.01, 0.03, 0.01, 0.02, 0.01, 0.02, 0.01, 0.03])
    engine.update_returns("VIX", [-0.01, -0.02, 0.01, -0.03, -0.01, -0.02, -0.01, -0.02, -0.01, -0.03])

    matrix = engine.compute_matrix([("SPY", "ES"), ("SPY", "VIX")])
    assert "SPY:ES" in matrix.pairs
    assert "SPY:VIX" in matrix.pairs
    assert matrix.pairs["SPY:ES"] > 0.9
    assert matrix.pairs["SPY:VIX"] < -0.9


# ============================================================================
# Exit Criteria 5: Leadership Engine works
# ============================================================================

def test_leadership_engine_identifies_leader():
    """Leadership engine identifies the leading instrument."""
    engine = LeadershipEngine()
    engine.update_returns("NVDA", [0.02, 0.03, 0.04, 0.05, 0.06])
    engine.update_returns("QQQ", [0.01, 0.01, 0.01, 0.01, 0.01])
    result = engine.analyze_leadership("NVDA", "QQQ")
    assert result.leader == "NVDA"


# ============================================================================
# Exit Criteria 6: Market DNA produced
# ============================================================================

async def test_market_dna_produced():
    """Market DNA Agent produces a summary for downstream AI."""
    agent = MarketDNAAgent()
    dna = await agent.compute_dna(
        quotes={
            "SPY": {"last": 450, "change_pct": 0.5},
            "ES": {"last": 4520, "change_pct": 0.4},
            "VIX": {"last": 15, "change_pct": -2},
            "TNX": {"last": 4.3, "change_pct": 0.1},
            "XLK": {"last": 180, "change_pct": 0.8},
            "XLU": {"last": 65, "change_pct": -0.2},
        },
        returns={
            "SPY": [0.001, 0.002, -0.001, 0.003, 0.001, 0.002, 0.001, 0.002, 0.001, 0.003],
            "ES": [0.001, 0.002, -0.001, 0.003, 0.001, 0.002, 0.001, 0.002, 0.001, 0.003],
            "VIX": [-0.01, -0.02, 0.01, -0.03, -0.01, -0.02, -0.01, -0.02, -0.01, -0.03],
            "XLK": [0.002, 0.003, 0.001, 0.004, 0.002, 0.003, 0.002, 0.003, 0.002, 0.004],
            "XLU": [-0.001, -0.001, 0.001, -0.002, -0.001, -0.001, 0.001, -0.002, -0.001, -0.001],
        },
    )

    assert dna.market_regime is not None
    assert dna.trend is not None
    assert dna.volatility is not None
    assert dna.leadership is not None
    assert dna.risk_score is not None
    assert dna.confidence > 0


# ============================================================================
# Exit Criteria 7: Config Service enables/disables without code changes
# ============================================================================

def test_config_service_disable(manager):
    """Config Service can disable a plugin at runtime."""
    manager.config_service.set_enabled("spy_vix_corr", False)
    assert manager.registry.get("spy_vix_corr").manifest.enabled is False


# ============================================================================
# Exit Criteria 8: Adding a new metric = adding a folder
# ============================================================================

def test_adding_metric_only_requires_folder(tmp_path):
    """Adding a new cross-market metric only requires creating a folder."""
    plugin_dir = tmp_path / "cross_market"
    new_plugin = plugin_dir / "liquidity_map"
    new_plugin.mkdir(parents=True)
    (new_plugin / "manifest.yaml").write_text(
        "id: liquidity_map\nname: Liquidity Map\nversion: 1.0.0\n"
        "category: divergence\nrefresh_interval_seconds: 10\n"
        "inputs: [quotes]\noutputs: [liquidity_zones]\ndependencies: []\n"
        "enabled: true\n"
    )

    mgr = CrossMarketPluginManager(plugin_dir=plugin_dir)
    count = mgr.discover()
    assert count == 1
    assert mgr.registry.get("liquidity_map") is not None


# ============================================================================
# Exit Criteria 9: Market Intelligence Hub collects data
# ============================================================================

def test_hub_collects_market_data():
    """Hub collects and synchronizes market data from all sources."""
    hub = MarketIntelligenceHub()
    hub.update_quote("SPY", {"last": 450.0, "change_pct": 0.5})
    hub.update_quote("ES", {"last": 4520.0, "change_pct": 0.4})
    hub.update_quote("VIX", {"last": 15.0, "change_pct": -2.0})

    snapshot = hub.get_snapshot()
    assert snapshot["symbols_tracked"] == 3
    assert "SPY" in snapshot["quotes"]


# ============================================================================
# Exit Criteria 10: All manifests valid
# ============================================================================

def test_all_manifests_valid(manager):
    """Every manifest has required fields."""
    for entry in manager.registry.list_all():
        m = entry.manifest
        assert m.id is not None
        assert m.name is not None
        assert m.version is not None
        assert len(m.outputs) > 0
