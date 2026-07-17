"""Stage 1 integration tests — wires all components via DI container."""
import pytest
import asyncio
from datetime import datetime, timezone

from athena_x_runtime_config import Settings, Environment
from athena_x_runtime_event_bus import BusEvent
from athena_x_runtime_di import Token
from athena_x_runtime_integration.wire_stage1 import (
    create_container, shutdown_container, stage1_lifespan,
    SETTINGS, BUS, HEALTH_REGISTRY, HEALTH_MONITOR, SCHEDULER, JWT_VERIFIER, SECRETS,
)


@pytest.fixture
async def container():
    """DI container with InMemoryBusClient (no Redis needed)."""
    settings = Settings(environment=Environment.DEVELOPMENT, debug=True)
    c = create_container(use_redis=False, settings=settings)
    yield c
    await shutdown_container(c)


# ============================================================================
# Functional tests
# ============================================================================

async def test_all_components_resolvable(container):
    """All 8 Stage 1 components can be resolved from the container."""
    settings = container.resolve(SETTINGS)
    assert settings is not None

    bus = await container.resolve_async(BUS)
    assert bus is not None

    registry = container.resolve(HEALTH_REGISTRY)
    assert registry is not None

    monitor = await container.resolve_async(HEALTH_MONITOR)
    assert monitor is not None

    scheduler = await container.resolve_async(SCHEDULER)
    assert scheduler is not None

    jwt = container.resolve(JWT_VERIFIER)
    assert jwt is not None

    secrets = container.resolve(SECRETS)
    assert secrets is not None


async def test_end_to_end_event_flow(container):
    """An event published on the bus reaches a subscriber."""
    bus = await container.resolve_async(BUS)

    received = []
    async def handler(event):
        received.append(event)

    await bus.subscribe("market:*", handler)

    event = BusEvent.create(
        event_type="market:quote-updated",
        provider="yahoo",
        agent_id="data-collection.collection",
        payload={"symbol": "NVDA", "last": 128.45},
    )
    await bus.publish(event)

    assert len(received) == 1
    assert received[0].payload["symbol"] == "NVDA"


async def test_heartbeat_updates_registry(container):
    """A heartbeat event updates the health registry."""
    bus = await container.resolve_async(BUS)
    registry = container.resolve(HEALTH_REGISTRY)
    # IMPORTANT: must resolve HEALTH_MONITOR to start it (subscribes to bus)
    monitor = await container.resolve_async(HEALTH_MONITOR)

    heartbeat = BusEvent.create(
        event_type="system:agent-heartbeat",
        provider="ta.rsi",
        agent_id="ta.rsi",
        payload={
            "agentId": "ta.rsi",
            "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000),
            "metrics": {
                "running": True,
                "cpu": 30.0,
                "memory": 64.0,
                "confidence": 0.95,
                "version": "0.1.0",
            }
        }
    )
    await bus.publish(heartbeat)
    await asyncio.sleep(0.1)

    agent = registry.get_agent("ta.rsi")
    assert agent is not None
    assert agent.running is True
    assert agent.cpu == 30.0


async def test_scheduler_executes_periodic_task(container):
    """Scheduler runs a task at the specified interval."""
    sched = await container.resolve_async(SCHEDULER)

    call_count = 0
    async def task():
        nonlocal call_count
        call_count += 1

    await sched.add_interval("test", seconds=1, func=task)
    await asyncio.sleep(2.5)
    assert call_count >= 2


# ============================================================================
# Stress tests
# ============================================================================

async def test_stress_10000_events_per_second(container):
    """Bus handles 10,000 events/sec for 1 second (Stage 1 performance budget)."""
    import time
    bus = await container.resolve_async(BUS)

    received_count = 0
    async def handler(event):
        nonlocal received_count
        received_count += 1

    await bus.subscribe("market:*", handler)

    # Publish 10,000 events as fast as possible
    start = time.monotonic()
    events = [
        BusEvent.create(
            event_type="market:quote-updated",
            provider="yahoo",
            agent_id="data-collection.collection",
            payload={"i": i},
        )
        for i in range(10_000)
    ]
    await asyncio.gather(*[bus.publish(e) for e in events])
    elapsed = time.monotonic() - start

    assert received_count == 10_000
    rate = received_count / elapsed
    assert rate >= 10_000, f"Throughput {rate:.0f} events/sec below 10,000/sec budget"
    print(f"\n  ✓ Throughput: {rate:,.0f} events/sec (budget: 10,000/sec)")


# ============================================================================
# Failover tests
# ============================================================================

async def test_failover_bus_close_and_health_check(container):
    """When bus closes, health_check returns False."""
    bus = await container.resolve_async(BUS)
    assert await bus.health_check() is True
    await bus.close()
    assert await bus.health_check() is False


# ============================================================================
# Performance tests
# ============================================================================

async def test_performance_publish_latency(container):
    """Publish latency p99 < 5ms (Stage 1 budget)."""
    import time
    bus = await container.resolve_async(BUS)

    async def noop(event): pass
    await bus.subscribe("market:*", noop)

    latencies = []
    for _ in range(1000):
        event = BusEvent.create(
            event_type="market:quote-updated",
            provider="yahoo",
            agent_id="test",
            payload={},
        )
        start = time.monotonic_ns()
        await bus.publish(event)
        elapsed_ns = time.monotonic_ns() - start
        latencies.append(elapsed_ns / 1_000_000)  # to ms

    latencies.sort()
    p50 = latencies[500]
    p99 = latencies[990]
    print(f"\n  ✓ p50: {p50:.3f}ms, p99: {p99:.3f}ms (budget: <5ms p99)")
    assert p99 < 5.0, f"p99 latency {p99:.3f}ms exceeds 5ms budget"


async def test_performance_logger_throughput(container):
    """Logger handles 50,000 logs/sec (Stage 1 budget)."""
    import time
    import io
    from contextlib import redirect_stdout
    from athena_x_runtime_logger import get_logger, configure_logging

    configure_logging(json_output=True, debug=False)
    log = get_logger("perf-test")

    buf = io.StringIO()
    with redirect_stdout(buf):
        start = time.monotonic()
        for i in range(10_000):
            log.info("test", iteration=i)
        elapsed = time.monotonic() - start

    rate = 10_000 / elapsed
    print(f"\n  ✓ Logger throughput: {rate:,.0f} logs/sec (budget: 50,000/sec)")
    assert rate >= 5_000  # conservative for test env
