"""Stage 8 acceptance tests - Options Intelligence Platform."""
import pytest
from pathlib import Path
from athena_x_engine_options_plugin_engine import OptionsPluginManager
from athena_x_plugin_options_base import OptionsPluginCategory


PLUGIN_DIR = Path(__file__).parent.parent.parent.parent / "plugins" / "options"


@pytest.fixture
def manager():
    mgr = OptionsPluginManager(plugin_dir=PLUGIN_DIR)
    mgr.discover()
    return mgr


# ============================================================================
# Exit Criteria 1: 40+ options plugins discovered
# ============================================================================

def test_40_plus_plugins_discovered(manager):
    """40+ options metric plugins are discovered from manifest.yaml files."""
    assert manager.registry.count() >= 40


# ============================================================================
# Exit Criteria 2: 8 categories present
# ============================================================================

def test_8_categories_present(manager):
    """All 8 options plugin categories are represented."""
    stats = manager.get_stats()
    by_cat = stats["by_category"]
    expected = ["volatility", "greeks", "dealer", "flow", "open_interest", "0dte", "dark_pool", "probability"]
    for cat in expected:
        assert cat in by_cat, f"Missing category: {cat}"


# ============================================================================
# Exit Criteria 3: Dependency graph resolves greeks before dealer metrics
# ============================================================================

def test_dependency_graph_gex_depends_on_gamma(manager):
    """GEX depends on gamma."""
    deps = manager.dependency_resolver.get_dependencies("gex")
    assert "gamma" in deps


def test_dependency_graph_no_cycles(manager):
    """No circular dependencies."""
    cycles = manager.dependency_resolver.detect_cycles()
    assert len(cycles) == 0


# ============================================================================
# Exit Criteria 4: Scheduler has configurable intervals
# ============================================================================

def test_scheduler_different_intervals(manager):
    """Different plugins have different refresh intervals."""
    stats = manager.scheduler.get_stats()
    schedules = stats["schedules"]
    intervals = set(s["interval"] for s in schedules)
    assert len(intervals) > 1


def test_greeks_refresh_faster_than_iv_rank(manager):
    """Greeks (1s) refresh faster than IV Rank (60s)."""
    stats = manager.scheduler.get_stats()
    schedules = {s["plugin_id"]: s for s in stats["schedules"]}
    if "delta" in schedules and "iv_rank" in schedules:
        assert schedules["delta"]["interval"] <= schedules["iv_rank"]["interval"]


# ============================================================================
# Exit Criteria 5: Config Service enables/disables without code changes
# ============================================================================

def test_config_service_disable(manager):
    """Config Service can disable a plugin at runtime."""
    manager.config_service.set_enabled("rho", False)
    assert manager.registry.get("rho").manifest.enabled is False


# ============================================================================
# Exit Criteria 6: 0DTE plugins exist
# ============================================================================

def test_0dte_plugins_exist(manager):
    """0DTE subsystem plugins are registered."""
    zero_dte = manager.list_by_category("0dte")
    assert len(zero_dte) >= 5


# ============================================================================
# Exit Criteria 7: Adding a new metric = adding a folder
# ============================================================================

def test_adding_metric_only_requires_folder(tmp_path):
    """Adding a new options metric only requires creating a folder."""
    plugin_dir = tmp_path / "options"
    new_plugin = plugin_dir / "volatility_arbitrage"
    new_plugin.mkdir(parents=True)
    (new_plugin / "manifest.yaml").write_text(
        "id: volatility_arbitrage\nname: Volatility Arbitrage\nversion: 1.0.0\n"
        "category: volatility\nrefresh_interval_seconds: 30\n"
        "inputs: [chain]\noutputs: [arb_signal]\ndependencies: [iv]\n"
        "enabled: true\n"
    )

    mgr = OptionsPluginManager(plugin_dir=plugin_dir)
    count = mgr.discover()
    assert count == 1
    assert mgr.registry.get("volatility_arbitrage") is not None


# ============================================================================
# Exit Criteria 8: All manifests have required fields
# ============================================================================

def test_all_manifests_valid(manager):
    """Every manifest has required fields."""
    for entry in manager.registry.list_all():
        m = entry.manifest
        assert m.id is not None
        assert m.name is not None
        assert m.version is not None
        assert len(m.outputs) > 0
        assert m.refresh_interval_seconds > 0


# ============================================================================
# Exit Criteria 9: Plugin stats include category breakdown
# ============================================================================

def test_stats_include_category_breakdown(manager):
    """Manager stats include per-category breakdown."""
    stats = manager.get_stats()
    assert "by_category" in stats
    assert len(stats["by_category"]) >= 8


# ============================================================================
# Exit Criteria 10: 0DTE Intelligence snapshot
# ============================================================================

async def test_0dte_intelligence_snapshot():
    """0DTE Intelligence Agent produces a snapshot for downstream."""
    from athena_x_agent_options_intelligence import ZeroDTEIntelligenceAgent
    # Inline FakePluginManager (don't import from test module)
    from athena_x_engine_plugin_engine import PluginRegistry, PluginManifest

    class FakePluginManager:
        def __init__(self):
            self.registry = PluginRegistry()
            for pid in ["gamma_flip", "gex", "expected_move", "iv_rank", "0dte_positioning", "intraday_risk"]:
                self.registry.register(PluginManifest.from_dict({
                    "id": pid, "name": pid.upper(), "category": "dealer", "layer": "2",
                    "timeframes": [], "inputs": [], "outputs": [pid],
                    "dependencies": [],
                }))
            from dataclasses import dataclass
            @dataclass
            class FakeOutput:
                value: object
            class FakePlugin:
                def __init__(self, pid):
                    self.pid = pid
                def compute(self, data=None):
                    values = {
                        "gamma_flip": {"gamma_flip_level": 4520.0, "dealer_gamma": "long"},
                        "gex": {"gex": 5000000},
                        "expected_move": {"expected_move_1d": 5.2},
                        "iv_rank": 67.5,
                        "0dte_positioning": {"positioning": "call_heavy"},
                        "intraday_risk": {"intraday_risk": "medium"},
                    }
                    return FakeOutput(value=values.get(self.pid))
            self._instances = {pid: FakePlugin(pid) for pid in ["gamma_flip", "gex", "expected_move", "iv_rank", "0dte_positioning", "intraday_risk"]}
        def get_instance(self, plugin_id):
            return self._instances.get(plugin_id)
        def load(self, plugin_id):
            return self._instances.get(plugin_id)

    mgr = FakePluginManager()
    agent = ZeroDTEIntelligenceAgent(mgr)
    snapshot = await agent.compute_snapshot("SPY")

    assert snapshot.symbol == "SPY"
    assert snapshot.gamma_flip_level is not None
    assert snapshot.dealer_gamma is not None
    assert snapshot.expected_move is not None
    assert snapshot.iv_regime is not None
    assert snapshot.positioning is not None
    assert snapshot.intraday_risk is not None
    assert snapshot.overall_confidence > 0
