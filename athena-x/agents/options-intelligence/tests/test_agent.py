"""Tests for SPY 0DTE Intelligence Agent."""
import pytest
from athena_x_agent_options_intelligence import ZeroDTEIntelligenceAgent, ZeroDTEIntelligenceSnapshot


class FakePluginManager:
    """Fake plugin manager for testing."""
    def __init__(self):
        from athena_x_engine_plugin_engine import PluginRegistry, PluginManifest
        self.registry = PluginRegistry()
        # Register some fake plugins
        for pid in ["gamma_flip", "gex", "expected_move", "iv_rank", "0dte_positioning", "intraday_risk"]:
            self.registry.register(PluginManifest.from_dict({
                "id": pid, "name": pid.upper(), "category": "dealer", "layer": "2",
                "timeframes": [], "inputs": [], "outputs": [pid],
                "dependencies": [],
            }))

        # Fake instances
        class FakePlugin:
            def __init__(self, pid):
                self.pid = pid
            def compute(self, data=None):
                from athena_x_plugin_options_base import OptionsPluginOutput, OptionsPluginCategory
                values = {
                    "gamma_flip": {"gamma_flip_level": 4520.0, "dealer_gamma": "long"},
                    "gex": {"gex": 5000000},
                    "expected_move": {"expected_move_1d": 5.2},
                    "iv_rank": 67.5,
                    "0dte_positioning": {"positioning": "call_heavy"},
                    "intraday_risk": {"intraday_risk": "medium"},
                }
                from dataclasses import dataclass
                @dataclass
                class FakeOutput:
                    value: object
                return FakeOutput(value=values.get(self.pid))

        self._instances = {pid: FakePlugin(pid) for pid in ["gamma_flip", "gex", "expected_move", "iv_rank", "0dte_positioning", "intraday_risk"]}

    def get_instance(self, plugin_id):
        return self._instances.get(plugin_id)

    def load(self, plugin_id):
        return self._instances.get(plugin_id)


@pytest.fixture
def manager():
    return FakePluginManager()


async def test_snapshot_includes_gamma_flip(manager):
    """Snapshot includes gamma flip level."""
    agent = ZeroDTEIntelligenceAgent(manager)
    snapshot = await agent.compute_snapshot("SPY")
    assert snapshot.gamma_flip_level == 4520.0


async def test_snapshot_includes_dealer_gamma(manager):
    """Snapshot includes dealer gamma direction."""
    agent = ZeroDTEIntelligenceAgent(manager)
    snapshot = await agent.compute_snapshot("SPY")
    assert snapshot.dealer_gamma in ("long", "short")


async def test_snapshot_includes_expected_move(manager):
    """Snapshot includes expected move."""
    agent = ZeroDTEIntelligenceAgent(manager)
    snapshot = await agent.compute_snapshot("SPY")
    assert snapshot.expected_move == 5.2


async def test_snapshot_includes_iv_regime(manager):
    """Snapshot includes IV regime classification."""
    agent = ZeroDTEIntelligenceAgent(manager)
    snapshot = await agent.compute_snapshot("SPY")
    assert snapshot.iv_regime in ("low", "normal", "high", "extreme")


async def test_snapshot_includes_positioning(manager):
    """Snapshot includes 0DTE positioning."""
    agent = ZeroDTEIntelligenceAgent(manager)
    snapshot = await agent.compute_snapshot("SPY")
    assert snapshot.positioning == "call_heavy"


async def test_snapshot_includes_intraday_risk(manager):
    """Snapshot includes intraday risk assessment."""
    agent = ZeroDTEIntelligenceAgent(manager)
    snapshot = await agent.compute_snapshot("SPY")
    assert snapshot.intraday_risk == "medium"


async def test_snapshot_has_overall_confidence(manager):
    """Snapshot includes overall confidence."""
    agent = ZeroDTEIntelligenceAgent(manager)
    snapshot = await agent.compute_snapshot("SPY")
    assert 0 < snapshot.overall_confidence <= 1.0


async def test_snapshot_event_published(manager):
    """Snapshot publishes options:0dte_intelligence_snapshot event."""
    from athena_x_runtime_event_bus import InMemoryBusClient

    bus = InMemoryBusClient()
    agent = ZeroDTEIntelligenceAgent(manager, event_bus=bus)

    received = []
    async def handler(event):
        received.append(event)
    await bus.subscribe("options:0dte_intelligence_snapshot", handler)

    await agent.compute_snapshot("SPY")

    assert len(received) == 1
    assert received[0].payload["symbol"] == "SPY"
    assert "gamma_flip_level" in received[0].payload
    await bus.close()
