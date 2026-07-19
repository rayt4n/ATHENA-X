"""Wire Stage 5 repositories + monitoring + backup."""
from __future__ import annotations
from athena_x_runtime_event_bus import InMemoryBusClient
from athena_x_runtime_db_events import DBEventEmitter
from athena_x_runtime_db_monitoring import DBMonitor
from athena_x_runtime_db_backup import BackupManager
from athena_x_runtime_in_memory_repository import (
    InMemoryMarketRepository, InMemoryOptionsRepository,
    InMemoryNewsRepository, InMemoryMacroRepository,
)


def create_stage5_container():
    """Create Stage 5 wiring: repositories + events + monitoring + backup."""
    bus = InMemoryBusClient()
    emitter = DBEventEmitter(bus=bus)
    monitor = DBMonitor()
    backup_mgr = BackupManager(backup_root="/tmp/athena-x-stage5-backups")

    return {
        "bus": bus,
        "event_emitter": emitter,
        "monitor": monitor,
        "backup_manager": backup_mgr,
        "market_repo": InMemoryMarketRepository(event_emitter=emitter, monitor=monitor),
        "options_repo": InMemoryOptionsRepository(event_emitter=emitter, monitor=monitor),
        "news_repo": InMemoryNewsRepository(event_emitter=emitter, monitor=monitor),
        "macro_repo": InMemoryMacroRepository(event_emitter=emitter, monitor=monitor),
    }
