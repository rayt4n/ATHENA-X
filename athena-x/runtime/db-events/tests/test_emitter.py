"""Tests for DB event emitter (Stage 5 req 11)."""
import pytest
from athena_x_runtime_db_events import DBEventEmitter, DBEventType
from athena_x_runtime_event_bus import InMemoryBusClient


@pytest.fixture
async def bus():
    b = InMemoryBusClient()
    yield b
    await b.close()


async def test_emit_market_written_event(bus):
    """Writing to canonical_market emits db:market-written."""
    received = []
    async def handler(event):
        received.append(event)
    await bus.subscribe("db:market-written", handler)

    emitter = DBEventEmitter(bus=bus)
    await emitter.emit_write(
        event_type=DBEventType.MARKET_WRITTEN,
        schema="canonical_market", table="quotes",
        record_id="rec-123", symbol="SPY",
        payload={"last_price": 450.0},
    )

    assert len(received) == 1
    assert received[0].event_type == "db:market-written"
    assert received[0].payload["schema"] == "canonical_market"
    assert received[0].payload["record_id"] == "rec-123"
    assert received[0].payload["symbol"] == "SPY"


async def test_emit_options_written_event(bus):
    emitter = DBEventEmitter(bus=bus)
    received = []
    async def handler(event):
        received.append(event)
    await bus.subscribe("db:options-written", handler)

    await emitter.emit_write(
        event_type=DBEventType.OPTIONS_WRITTEN,
        schema="canonical_options", table="chains",
        record_id="rec-opt-1", symbol="NVDA",
    )
    assert len(received) == 1


async def test_emit_includes_supersession(bus):
    """When a record supersedes another, the event includes superseded_record_id."""
    emitter = DBEventEmitter(bus=bus)
    received = []
    async def handler(event):
        received.append(event)
    await bus.subscribe("db:market-written", handler)

    await emitter.emit_write(
        event_type=DBEventType.MARKET_WRITTEN,
        schema="canonical_market", table="quotes",
        record_id="rec-new", symbol="SPY",
        superseded_record_id="rec-old",
    )
    assert received[0].payload["superseded_record_id"] == "rec-old"


async def test_no_bus_no_error():
    """Emitter without bus doesn't error (no-op)."""
    emitter = DBEventEmitter(bus=None)
    await emitter.emit_write(
        event_type=DBEventType.MARKET_WRITTEN,
        schema="canonical_market", table="quotes",
        record_id="rec-1",
    )
    assert emitter.event_count == 0


def test_all_db_event_types_defined():
    """All 11 db:* event types are defined."""
    assert DBEventType.MARKET_WRITTEN.value == "db:market-written"
    assert DBEventType.OPTIONS_WRITTEN.value == "db:options-written"
    assert DBEventType.NEWS_WRITTEN.value == "db:news-written"
    assert DBEventType.MACRO_WRITTEN.value == "db:macro-written"
    assert DBEventType.FORECAST_WRITTEN.value == "db:forecast-written"
    assert DBEventType.REPORT_WRITTEN.value == "db:report-written"
    assert DBEventType.BACKTEST_WRITTEN.value == "db:backtest-written"
