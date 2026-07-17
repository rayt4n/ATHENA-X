"""Wire all Stage 1 components together via the DI container.

This is the canonical wiring used by the FastAPI backend at startup.
"""
from __future__ import annotations
import asyncio
from typing import AsyncIterator
from contextlib import asynccontextmanager

from athena_x_runtime_config import Settings, get_settings
from athena_x_runtime_logger import configure_logging, get_logger
from athena_x_runtime_event_bus import InMemoryBusClient, RedisBusClient, BusClient
from athena_x_runtime_health_monitor import HealthRegistry, HealthMonitor
from athena_x_runtime_scheduler import Scheduler
from athena_x_runtime_di import Container, Token
from athena_x_runtime_auth import JWTVerifier
from athena_x_runtime_secrets import SecretsManager


# Tokens for DI
SETTINGS = Token[Settings]("settings")
BUS = Token[BusClient]("bus")
HEALTH_REGISTRY = Token[HealthRegistry]("health_registry")
HEALTH_MONITOR = Token[HealthMonitor]("health_monitor")
SCHEDULER = Token[Scheduler]("scheduler")
JWT_VERIFIER = Token[JWTVerifier]("jwt_verifier")
SECRETS = Token[SecretsManager]("secrets")


def create_container(
    *,
    use_redis: bool = False,
    settings: Settings | None = None,
) -> Container:
    """Create a DI container wired with all Stage 1 components.

    Args:
        use_redis: if True, use RedisBusClient (requires Redis running).
                   If False, use InMemoryBusClient (for dev + tests).
        settings: optional pre-built Settings instance. If None, loads from env.
    """
    if settings is None:
        settings = get_settings()

    # Configure logging based on settings
    configure_logging(debug=settings.debug, json_output=not settings.is_development())

    container = Container()
    container.register_singleton(SETTINGS, settings)
    container.register_singleton(SECRETS, SecretsManager())

    # Event bus — async singleton (one instance, shared across all resolves)
    if use_redis:
        async def make_redis_bus(c: Container) -> BusClient:
            s = c.resolve(SETTINGS)
            bus = RedisBusClient(
                redis_url=s.redis.url,
                backpressure_max_age_ms=s.event_bus.backpressure_max_age_ms,
            )
            await bus.connect()
            return bus
        container.register_async_singleton(BUS, make_redis_bus)
    else:
        async def make_inmem_bus(c: Container) -> BusClient:
            s = c.resolve(SETTINGS)
            return InMemoryBusClient(backpressure_max_age_ms=s.event_bus.backpressure_max_age_ms)
        container.register_async_singleton(BUS, make_inmem_bus)

    # Health registry (singleton)
    container.register_singleton(HEALTH_REGISTRY, HealthRegistry(
        heartbeat_miss_threshold=settings.health_monitor.heartbeat_miss_threshold,
        heartbeat_interval_seconds=settings.health_monitor.heartbeat_interval_seconds,
    ))

    # Health monitor (async singleton — needs bus, must be shared)
    async def make_health_monitor(c: Container) -> HealthMonitor:
        bus = await c.resolve_async(BUS)
        registry = c.resolve(HEALTH_REGISTRY)
        s = c.resolve(SETTINGS)
        monitor = HealthMonitor(
            bus=bus,
            registry=registry,
            heartbeat_interval_seconds=s.health_monitor.heartbeat_interval_seconds,
            heartbeat_miss_threshold=s.health_monitor.heartbeat_miss_threshold,
        )
        await monitor.start()
        return monitor
    container.register_async_singleton(HEALTH_MONITOR, make_health_monitor)

    # Scheduler (async singleton)
    async def make_scheduler(c: Container) -> Scheduler:
        sched = Scheduler()
        await sched.start()
        return sched
    container.register_async_singleton(SCHEDULER, make_scheduler)

    # JWT verifier (singleton)
    container.register_singleton(JWT_VERIFIER, JWTVerifier(
        supabase_url=settings.supabase.url,
        supabase_anon_key=settings.supabase.anon_key.get_secret_value(),
    ))

    return container


async def shutdown_container(container: Container) -> None:
    """Gracefully shut down all async components."""
    if container.has(SCHEDULER):
        sched = await container.resolve_async(SCHEDULER)
        await sched.shutdown()
    if container.has(HEALTH_MONITOR):
        monitor = await container.resolve_async(HEALTH_MONITOR)
        await monitor.stop()
    if container.has(BUS):
        bus = await container.resolve_async(BUS)
        await bus.close()


@asynccontextmanager
async def stage1_lifespan(use_redis: bool = False) -> AsyncIterator[Container]:
    """Context manager that wires Stage 1, yields the container, and shuts down.

    Usage:
        async with stage1_lifespan() as container:
            bus = await container.resolve_async(BUS)
            await bus.publish(event)
    """
    container = create_container(use_redis=use_redis)
    try:
        yield container
    finally:
        await shutdown_container(container)
