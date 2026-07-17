"""Wire Stage 2 components into a DI container."""
from __future__ import annotations
from pathlib import Path
from athena_x_runtime_di import Container, Token
from athena_x_runtime_config import Settings
from athena_x_runtime_event_bus import InMemoryBusClient, BusClient
from athena_x_runtime_raw_archival import RawArchiver
from athena_x_runtime_data_freshness import FreshnessTracker
from athena_x_runtime_session_awareness import SessionDetector
from athena_x_runtime_health_monitor import HealthRegistry, HealthMonitor
from athena_x_provider_simulated import SimulatedAdapter
from athena_x_provider_failover import FailoverChain
from athena_x_collector_base import CollectorRegistry


# Tokens
ARCHIVER = Token[RawArchiver]("archiver")
FRESHNESS = Token[FreshnessTracker]("freshness")
SESSION_DETECTOR = Token[SessionDetector]("session_detector")
FAILOVER_CHAIN = Token[FailoverChain]("failover_chain")
COLLECTOR_REGISTRY = Token[CollectorRegistry]("collector_registry")


def create_stage2_container(
    *,
    settings: Settings | None = None,
    archival_path: str | Path = "/tmp/athena-x-raw-landing",
) -> Container:
    """Create a DI container wired with all Stage 1 + Stage 2 components."""
    from athena_x_runtime_integration.wire_stage1 import create_container as create_stage1

    # Start from Stage 1 wiring (event bus, logger, etc.)
    container = create_stage1(use_redis=False, settings=settings)

    # Stage 2 additions
    archiver = RawArchiver(base_path=archival_path)
    container.register_singleton(ARCHIVER, archiver)

    freshness = FreshnessTracker()
    container.register_singleton(FRESHNESS, freshness)

    container.register_singleton(SESSION_DETECTOR, SessionDetector())

    # Provider failover chain (using SimulatedAdapter for dev)
    simulated = SimulatedAdapter(
        seed=42,
        archiver=archiver,
        freshness_tracker=freshness,
    )
    container.register_singleton(FAILOVER_CHAIN, FailoverChain(
        providers=[simulated],
        bus=container.resolve(Token[BusClient]("bus")) if container.has(Token[BusClient]("bus")) else None,
    ))

    container.register_singleton(COLLECTOR_REGISTRY, CollectorRegistry())

    return container
