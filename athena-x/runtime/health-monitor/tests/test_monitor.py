"""Tests for HealthMonitor."""
import pytest
import asyncio
from datetime import datetime, timezone
from athena_x_runtime_event_bus import BusEvent, InMemoryBusClient
from athena_x_runtime_health_monitor import HealthRegistry, HealthMonitor


@pytest.fixture
async def setup():
    bus = InMemoryBusClient()
    registry = HealthRegistry(heartbeat_miss_threshold=2, heartbeat_interval_seconds=1)
    monitor = HealthMonitor(bus, registry, heartbeat_interval_seconds=1, heartbeat_miss_threshold=2)
    await monitor.start()
    yield bus, registry, monitor
    await monitor.stop()
    await bus.close()


async def test_heartbeat_updates_registry(setup):
    bus, registry, monitor = setup

    heartbeat = BusEvent.create(
        event_type="system:agent-heartbeat",
        provider="ta.rsi",
        agent_id="ta.rsi",
        payload={
            "agentId": "ta.rsi",
            "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000),
            "metrics": {
                "running": True,
                "cpu": 45.0,
                "memory": 128.5,
                "apiLatency": 12.0,
                "queueLength": 3,
                "errorCount": 0,
                "restartCount": 0,
                "confidence": 0.95,
                "version": "0.1.0",
            }
        }
    )
    await bus.publish(heartbeat)

    # Give the handler time to run
    await asyncio.sleep(0.05)

    agent = registry.get_agent("ta.rsi")
    assert agent is not None
    assert agent.running is True
    assert agent.cpu == 45.0
    assert agent.memory == 128.5
    assert agent.confidence == 0.95


async def test_provider_health_updates_registry(setup):
    bus, registry, monitor = setup

    event = BusEvent.create(
        event_type="system:provider-health-updated",
        provider="yahoo",
        agent_id="data-collection.collection",
        payload={
            "provider": "yahoo",
            "status": "connected",
            "delay": 120.0,
            "missingBars": 0,
            "missingTicks": 0,
            "apiErrors": 0,
            "failoverCount": 0,
            "freshness": 1000.0,
            "reliabilityScore": 0.99,
        }
    )
    await bus.publish(event)
    await asyncio.sleep(0.05)

    p = registry.get_provider("yahoo")
    assert p is not None
    assert p.connection == "connected"
    assert p.delay == 120.0
    assert p.reliability_score == 0.99


async def test_failure_checker_emits_supervisor_event(setup):
    """When an agent misses heartbeats, supervisor:agent-failing is published."""
    bus, registry, monitor = setup

    # Track supervisor events
    supervisor_events = []

    async def supervisor_handler(event):
        supervisor_events.append(event)

    await bus.subscribe("supervisor:*", supervisor_handler)

    # Register an agent with an old heartbeat (will be detected as failing)
    from datetime import timedelta
    from athena_x_runtime_health_monitor import AgentHealth
    registry.update_agent(AgentHealth(
        agentId="ta.dead",
        running=True,
        lastUpdate=datetime.now(timezone.utc) - timedelta(seconds=30),
    ))

    # Wait for the failure checker to run (interval is 1 second)
    await asyncio.sleep(2.5)

    assert len(supervisor_events) > 0
    assert supervisor_events[0].event_type == "supervisor:agent-failing"
    assert supervisor_events[0].payload["agentId"] == "ta.dead"
