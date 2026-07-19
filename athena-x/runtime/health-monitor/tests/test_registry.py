"""Tests for HealthRegistry."""
import pytest
from datetime import datetime, timezone, timedelta
from athena_x_runtime_health_monitor import AgentHealth, ProviderHealth, HealthRegistry


@pytest.fixture
def registry():
    return HealthRegistry(heartbeat_miss_threshold=3, heartbeat_interval_seconds=5)


def test_update_and_get_agent(registry):
    """Agent health can be updated and retrieved."""
    h = AgentHealth(agentId="ta.rsi", running=True, lastUpdate=datetime.now(timezone.utc))
    registry.update_agent(h)
    retrieved = registry.get_agent("ta.rsi")
    assert retrieved is not None
    assert retrieved.agent_id == "ta.rsi"
    assert retrieved.running is True


def test_stale_agent_marked_not_running(registry):
    """Agent that missed heartbeats is marked as not running."""
    old_time = datetime.now(timezone.utc) - timedelta(seconds=30)
    h = AgentHealth(agentId="ta.rsi", running=True, lastUpdate=old_time)
    registry.update_agent(h)

    retrieved = registry.get_agent("ta.rsi")
    assert retrieved is not None
    assert retrieved.running is False  # marked stale


def test_list_failing_agents(registry):
    """list_failing_agents returns only stale agents."""
    now = datetime.now(timezone.utc)
    old = now - timedelta(seconds=30)

    registry.update_agent(AgentHealth(agentId="ta.rsi", running=True, lastUpdate=now))
    registry.update_agent(AgentHealth(agentId="ta.macd", running=True, lastUpdate=old))

    failing = registry.list_failing_agents()
    assert len(failing) == 1
    assert failing[0].agent_id == "ta.macd"


def test_update_and_get_provider(registry):
    p = ProviderHealth(provider="yahoo", connection="connected", delay=10.0)
    registry.update_provider(p)
    retrieved = registry.get_provider("yahoo")
    assert retrieved is not None
    assert retrieved.provider == "yahoo"
    assert retrieved.connection == "connected"


def test_list_degraded_providers(registry):
    registry.update_provider(ProviderHealth(provider="yahoo", connection="connected"))
    registry.update_provider(ProviderHealth(provider="finnhub", connection="degraded"))
    registry.update_provider(ProviderHealth(provider="polygon", connection="disconnected"))

    degraded = registry.list_degraded_providers()
    assert len(degraded) == 2
    degraded_names = {p.provider for p in degraded}
    assert degraded_names == {"finnhub", "polygon"}


def test_clear(registry):
    registry.update_agent(AgentHealth(agentId="ta.rsi", running=True))
    registry.update_provider(ProviderHealth(provider="yahoo", connection="connected"))
    registry.clear()
    assert registry.list_agents() == []
    assert registry.list_providers() == []
