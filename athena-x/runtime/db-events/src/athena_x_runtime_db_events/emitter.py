"""Database event emitter - Stage 5 req 11.

Every database write emits an event:
  - db:market-written
  - db:options-written
  - db:news-written
  - db:macro-written
  - db:forecast-written
  - db:report-written
  - db:backtest-written

Downstream services subscribe - no polling.
"""
from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from athena_x_runtime_event_bus import BusClient, BusEvent
from athena_x_runtime_logger import get_logger

log = get_logger("runtime.db-events")


class DBEventType(str, Enum):
    MARKET_WRITTEN = "db:market-written"
    OPTIONS_WRITTEN = "db:options-written"
    NEWS_WRITTEN = "db:news-written"
    MACRO_WRITTEN = "db:macro-written"
    VALIDATION_WRITTEN = "db:validation-written"
    INTELLIGENCE_WRITTEN = "db:intelligence-written"
    FORECAST_WRITTEN = "db:forecast-written"
    REPORT_WRITTEN = "db:report-written"
    BACKTEST_WRITTEN = "db:backtest-written"
    REPLAY_WRITTEN = "db:replay-written"
    MEMORY_WRITTEN = "db:memory-written"


class DBEventEmitter:
    """Emits db:* events when records are written to databases.

    Usage:
        emitter = DBEventEmitter(bus=bus)
        await emitter.emit_write(
            event_type=DBEventType.MARKET_WRITTEN,
            schema="canonical_market",
            table="quotes",
            record_id="rec-123",
            symbol="SPY",
            payload={"last_price": 450.0},
        )
    """

    def __init__(self, bus: BusClient | None = None):
        self._bus = bus
        self._event_count = 0

    async def emit_write(
        self,
        *,
        event_type: DBEventType,
        schema: str,
        table: str,
        record_id: str,
        symbol: str | None = None,
        payload: Any = None,
        superseded_record_id: str | None = None,
    ) -> None:
        """Emit a db:*-written event."""
        if self._bus is None:
            return

        event = BusEvent.create(
            event_type=event_type.value,
            provider=schema,
            agent_id=f"db.{schema}",
            payload={
                "schema": schema,
                "table": table,
                "record_id": record_id,
                "symbol": symbol,
                "superseded_record_id": superseded_record_id,
                "written_at": datetime.now(timezone.utc).isoformat(),
                "data": payload,
            },
            confidence=1.0,
        )
        await self._bus.publish(event)
        self._event_count += 1
        log.debug("db_event_emitted",
                  event_type=event_type.value,
                  schema=schema,
                  record_id=record_id)

    @property
    def event_count(self) -> int:
        return self._event_count
