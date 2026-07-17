"""In-memory MacroRepository."""
from __future__ import annotations
from datetime import datetime
from threading import RLock
from typing import Any

from athena_x_runtime_repository_interface import WriteResult, QueryResult
from athena_x_runtime_repository_interface.base import BaseRepository
from athena_x_runtime_db_events import DBEventEmitter, DBEventType
from athena_x_runtime_db_monitoring import DBMonitor


class InMemoryMacroRepository(BaseRepository):
    schema_name = "canonical_macro"

    def __init__(self, event_emitter=None, monitor=None):
        self._indicators: dict[str, dict] = {}  # (indicator, region) → record
        self._lock = RLock()
        self._emitter = event_emitter or DBEventEmitter()
        self._monitor = monitor or DBMonitor()

    async def write_indicator(self, record: Any) -> WriteResult:
        with self._monitor.track("write_indicator"):
            with self._lock:
                record_id = self._generate_record_id()
                indicator = record.get("indicator", "")
                region = record.get("region", "")
                key = f"{indicator}:{region}"
                stored = {"record_id": record_id, "data": record, "written_at": self._now().isoformat()}
                self._indicators[key] = stored

            result = self._make_write_result(record_id, "indicators", event_published=True)
            await self._emitter.emit_write(
                event_type=DBEventType.MACRO_WRITTEN,
                schema=self.schema_name, table="indicators",
                record_id=record_id, symbol=None, payload=record,
            )
            return result

    async def read_indicator(self, indicator: str, region: str) -> Any | None:
        with self._monitor.track("read_indicator"):
            with self._lock:
                key = f"{indicator}:{region}"
                stored = self._indicators.get(key)
                return stored["data"] if stored else None

    async def query_indicators(
        self, region=None, start=None, end=None,
    ) -> QueryResult:
        with self._monitor.track("query_indicators"):
            with self._lock:
                results = []
                for stored in self._indicators.values():
                    record = stored["data"]
                    if region and record.get("region") != region:
                        continue
                    results.append(record)
                return QueryResult(records=results, count=len(results))
