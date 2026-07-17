"""In-memory MarketRepository for tests + dev (no Postgres required).

Implements the MarketRepository protocol with in-memory storage.
Supports:
  - write_quote / read_quote
  - write_bar / query_bars
  - supersede (immutable records, Stage 5 req 7)
  - get_history (including superseded records)
  - Event emission (db:market-written)
  - Performance monitoring
"""
from __future__ import annotations
from datetime import datetime, timezone
from threading import RLock
from typing import Any
from collections import defaultdict

from athena_x_runtime_repository_interface import WriteResult, QueryResult, RepositoryError
from athena_x_runtime_repository_interface.base import BaseRepository
from athena_x_runtime_db_events import DBEventEmitter, DBEventType
from athena_x_runtime_db_monitoring import DBMonitor
from athena_x_runtime_logger import get_logger

log = get_logger("repository.in-memory.market")


class InMemoryMarketRepository(BaseRepository):
    """In-memory implementation of MarketRepository.

    Schema: canonical_market
    Writer: Market Standardization Agent ONLY (enforced by convention)
    """

    schema_name = "canonical_market"

    def __init__(
        self,
        event_emitter: DBEventEmitter | None = None,
        monitor: DBMonitor | None = None,
    ):
        self._quotes: dict[str, dict] = {}  # symbol → latest record
        self._bars: dict[str, list[dict]] = defaultdict(list)  # (symbol,tf) → list of bars
        self._all_records: list[dict] = []  # all records (for history + replay)
        self._superseded: dict[str, str] = {}  # old_record_id → new_record_id
        self._lock = RLock()
        self._emitter = event_emitter or DBEventEmitter()
        self._monitor = monitor or DBMonitor()

    async def write_quote(self, record: Any) -> WriteResult:
        """Write a market quote."""
        with self._monitor.track("write_quote"):
            with self._lock:
                record_id = self._generate_record_id()
                symbol = record.get("symbol", "")
                stored = {
                    "record_id": record_id,
                    "schema": self.schema_name,
                    "table": "quotes",
                    "data": record,
                    "written_at": self._now().isoformat(),
                    "superseded_by": None,
                }
                self._quotes[symbol] = stored
                self._all_records.append(stored)

            result = self._make_write_result(record_id, "quotes", event_published=True)
            await self._emitter.emit_write(
                event_type=DBEventType.MARKET_WRITTEN,
                schema=self.schema_name,
                table="quotes",
                record_id=record_id,
                symbol=symbol,
                payload=record,
            )
            return result

    async def read_quote(self, symbol: str) -> Any | None:
        """Read the latest quote for a symbol."""
        with self._monitor.track("read_quote"):
            with self._lock:
                stored = self._quotes.get(symbol)
                if stored is None:
                    return None
                return stored["data"]

    async def write_bar(self, record: Any) -> WriteResult:
        """Write an OHLCV bar."""
        with self._monitor.track("write_bar"):
            with self._lock:
                record_id = self._generate_record_id()
                symbol = record.get("symbol", "")
                timeframe = record.get("timeframe", "1m")
                key = f"{symbol}:{timeframe}"
                stored = {
                    "record_id": record_id,
                    "schema": self.schema_name,
                    "table": "bars",
                    "data": record,
                    "written_at": self._now().isoformat(),
                    "superseded_by": None,
                }
                self._bars[key].append(stored)
                self._all_records.append(stored)

            result = self._make_write_result(record_id, "bars", event_published=True)
            await self._emitter.emit_write(
                event_type=DBEventType.MARKET_WRITTEN,
                schema=self.schema_name,
                table="bars",
                record_id=record_id,
                symbol=symbol,
                payload=record,
            )
            return result

    async def query_bars(
        self, symbol: str, timeframe: str,
        start: datetime, end: datetime,
    ) -> QueryResult:
        """Query historical bars."""
        with self._monitor.track("query_bars"):
            with self._lock:
                key = f"{symbol}:{timeframe}"
                bars = self._bars.get(key, [])
                # Filter by time range
                result = []
                for b in bars:
                    ts = b["data"].get("timestamp")
                    if ts is None:
                        continue
                    if isinstance(ts, str):
                        ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    if start <= ts <= end:
                        result.append(b["data"])
                return QueryResult(records=result, count=len(result))

    async def supersede(self, record_id: str, corrected: Any) -> WriteResult:
        """Insert a corrected version, marking old as superseded (Stage 5 req 7).

        Immutable records: never UPDATE - insert new + mark old as superseded.
        """
        with self._monitor.track("supersede"):
            with self._lock:
                # Mark old record as superseded
                self._superseded[record_id] = "pending"
                # Find + mark in all_records
                for r in self._all_records:
                    if r["record_id"] == record_id:
                        r["superseded_by"] = "pending"

                # Insert corrected version
                new_id = self._generate_record_id()
                symbol = corrected.get("symbol", "")
                stored = {
                    "record_id": new_id,
                    "schema": self.schema_name,
                    "table": "quotes",
                    "data": corrected,
                    "written_at": self._now().isoformat(),
                    "superseded_by": None,
                    "supersedes": record_id,
                }
                self._all_records.append(stored)
                # Update quotes with corrected
                self._quotes[symbol] = stored

                # Update superseded link
                self._superseded[record_id] = new_id
                for r in self._all_records:
                    if r["record_id"] == record_id:
                        r["superseded_by"] = new_id

            result = self._make_write_result(
                new_id, "quotes",
                superseded_record_id=record_id,
                event_published=True,
            )
            await self._emitter.emit_write(
                event_type=DBEventType.MARKET_WRITTEN,
                schema=self.schema_name,
                table="quotes",
                record_id=new_id,
                symbol=symbol,
                payload=corrected,
                superseded_record_id=record_id,
            )
            return result

    async def get_history(self, symbol: str, limit: int = 100) -> QueryResult:
        """Get historical records for a symbol (including superseded)."""
        with self._monitor.track("get_history"):
            with self._lock:
                records = [
                    r for r in self._all_records
                    if r["data"].get("symbol") == symbol
                ]
                return QueryResult(
                    records=records[-limit:],
                    count=len(records),
                )

    def get_stats(self) -> dict:
        with self._lock:
            return {
                "quotes_count": len(self._quotes),
                "bars_count": sum(len(v) for v in self._bars.values()),
                "total_records": len(self._all_records),
                "superseded_count": len(self._superseded),
            }

    async def dump_schema(self, schema: str) -> list[dict]:
        """Dump all records (for backup)."""
        with self._lock:
            return list(self._all_records)

    async def restore_schema(self, schema: str, data: list[dict]) -> int:
        """Restore records from backup."""
        with self._lock:
            self._all_records = list(data)
            for r in data:
                symbol = r["data"].get("symbol", "")
                if r["table"] == "quotes":
                    self._quotes[symbol] = r
                elif r["table"] == "bars":
                    timeframe = r["data"].get("timeframe", "1m")
                    key = f"{symbol}:{timeframe}"
                    self._bars[key].append(r)
            return len(data)
