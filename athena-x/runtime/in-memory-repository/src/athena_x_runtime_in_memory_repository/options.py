"""In-memory OptionsRepository."""
from __future__ import annotations
from datetime import datetime, date
from threading import RLock
from typing import Any
from collections import defaultdict

from athena_x_runtime_repository_interface import WriteResult, QueryResult
from athena_x_runtime_repository_interface.base import BaseRepository
from athena_x_runtime_db_events import DBEventEmitter, DBEventType
from athena_x_runtime_db_monitoring import DBMonitor


class InMemoryOptionsRepository(BaseRepository):
    schema_name = "canonical_options"

    def __init__(self, event_emitter=None, monitor=None):
        self._chains: dict[str, dict] = {}  # (symbol, expiry) → chain
        self._lock = RLock()
        self._emitter = event_emitter or DBEventEmitter()
        self._monitor = monitor or DBMonitor()

    async def write_chain(self, record: Any) -> WriteResult:
        with self._monitor.track("write_chain"):
            with self._lock:
                record_id = self._generate_record_id()
                symbol = record.get("symbol", "")
                expiry = str(record.get("expiry", ""))
                key = f"{symbol}:{expiry}"
                stored = {"record_id": record_id, "data": record, "written_at": self._now().isoformat()}
                self._chains[key] = stored

            result = self._make_write_result(record_id, "chains", event_published=True)
            await self._emitter.emit_write(
                event_type=DBEventType.OPTIONS_WRITTEN,
                schema=self.schema_name, table="chains",
                record_id=record_id, symbol=symbol, payload=record,
            )
            return result

    async def read_chain(self, symbol: str, expiry: Any) -> Any | None:
        with self._monitor.track("read_chain"):
            with self._lock:
                key = f"{symbol}:{expiry}"
                stored = self._chains.get(key)
                return stored["data"] if stored else None

    async def query_chains(self, symbol: str, start: datetime, end: datetime) -> QueryResult:
        with self._monitor.track("query_chains"):
            with self._lock:
                results = []
                for key, stored in self._chains.items():
                    if key.startswith(f"{symbol}:"):
                        results.append(stored["data"])
                return QueryResult(records=results, count=len(results))

    async def supersede(self, record_id: str, corrected: Any) -> WriteResult:
        # Simplified - just overwrite
        return await self.write_chain(corrected)
