"""Tests for InMemoryMarketRepository (Stage 5)."""
import pytest
from datetime import datetime, timezone, timedelta
from athena_x_runtime_in_memory_repository import InMemoryMarketRepository
from athena_x_runtime_repository_interface import MarketRepository
from athena_x_runtime_db_events import DBEventEmitter
from athena_x_runtime_event_bus import InMemoryBusClient


@pytest.fixture
async def setup():
    bus = InMemoryBusClient()
    emitter = DBEventEmitter(bus=bus)
    repo = InMemoryMarketRepository(event_emitter=emitter)
    yield bus, emitter, repo
    await bus.close()


def test_implements_market_repository_protocol(setup):
    """InMemoryMarketRepository implements MarketRepository protocol."""
    _, _, repo = setup
    assert isinstance(repo, MarketRepository) or hasattr(repo, "write_quote")


async def test_write_and_read_quote(setup):
    """Write a quote, then read it back."""
    _, _, repo = setup
    record = {"symbol": "SPY", "last_price": 450.0, "timestamp": datetime.now(timezone.utc).isoformat()}
    result = await repo.write_quote(record)
    assert result.record_id is not None
    assert result.schema == "canonical_market"

    read = await repo.read_quote("SPY")
    assert read is not None
    assert read["last_price"] == 450.0


async def test_write_and_query_bars(setup):
    """Write bars, then query by time range."""
    _, _, repo = setup
    base = datetime.now(timezone.utc)
    for i in range(5):
        await repo.write_bar({
            "symbol": "SPY", "timeframe": "1m",
            "timestamp": (base + timedelta(minutes=i)).isoformat(),
            "open": 450 + i, "high": 451 + i, "low": 449 + i, "close": 450 + i, "volume": 1000,
        })

    result = await repo.query_bars(
        "SPY", "1m",
        start=base, end=base + timedelta(minutes=10),
    )
    assert result.count == 5


async def test_supersede_creates_new_record(setup):
    """Supersession inserts new record (Stage 5 req 7 - immutable)."""
    _, _, repo = setup
    # Write original
    original = {"symbol": "SPY", "last_price": 450.0, "timestamp": datetime.now(timezone.utc).isoformat()}
    write1 = await repo.write_quote(original)

    # Supersede with corrected
    corrected = {"symbol": "SPY", "last_price": 451.0, "timestamp": datetime.now(timezone.utc).isoformat()}
    write2 = await repo.supersede(write1.record_id, corrected)

    assert write2.record_id != write1.record_id
    assert write2.superseded_record_id == write1.record_id

    # Read returns corrected version
    read = await repo.read_quote("SPY")
    assert read["last_price"] == 451.0


async def test_get_history_includes_superseded(setup):
    """History includes superseded records (audit trail)."""
    _, _, repo = setup
    original = {"symbol": "SPY", "last_price": 450.0, "timestamp": datetime.now(timezone.utc).isoformat()}
    write1 = await repo.write_quote(original)
    corrected = {"symbol": "SPY", "last_price": 451.0, "timestamp": datetime.now(timezone.utc).isoformat()}
    await repo.supersede(write1.record_id, corrected)

    history = await repo.get_history("SPY")
    assert history.count >= 2  # original + corrected


async def test_write_emits_db_event(setup):
    """Writing emits db:market-written event (Stage 5 req 11)."""
    bus, _, repo = setup
    received = []
    async def handler(event):
        received.append(event)
    await bus.subscribe("db:market-written", handler)

    await repo.write_quote({"symbol": "SPY", "last_price": 450.0, "timestamp": datetime.now(timezone.utc).isoformat()})

    assert len(received) == 1
    assert received[0].payload["schema"] == "canonical_market"
    assert received[0].payload["symbol"] == "SPY"


async def test_supersede_emits_event_with_supersession(setup):
    """Supersession events include superseded_record_id."""
    bus, _, repo = setup
    received = []
    async def handler(event):
        received.append(event)
    await bus.subscribe("db:market-written", handler)

    write1 = await repo.write_quote({"symbol": "SPY", "last_price": 450.0, "timestamp": datetime.now(timezone.utc).isoformat()})
    await repo.supersede(write1.record_id, {"symbol": "SPY", "last_price": 451.0, "timestamp": datetime.now(timezone.utc).isoformat()})

    # 2 events: original write + supersede
    assert len(received) == 2
    supersede_event = received[1]
    assert supersede_event.payload["superseded_record_id"] == write1.record_id


def test_get_stats(setup):
    """get_stats returns repository statistics."""
    _, _, repo = setup
    stats = repo.get_stats()
    assert "quotes_count" in stats
    assert "bars_count" in stats
    assert "total_records" in stats
    assert "superseded_count" in stats
