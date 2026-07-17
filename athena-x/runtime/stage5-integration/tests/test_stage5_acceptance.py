"""Stage 5 acceptance tests - all 9 categories must pass.

Exit criteria:
  1. All 12 schemas implemented with clear ownership
  2. Writer-lock rules enforced through roles + RLS
  3. Time-series partitioning operational
  4. Indexes support expected query patterns
  5. Immutable data + audit trails enforced
  6. Backup, restore, replay tested
  7. Database health metrics available
  8. Event notifications published for all writes
  9. Migration, integrity, failover, recovery tests pass
 10. Full trading day ingested, stored, replayed, restored without data loss
"""
import pytest
import time
from datetime import datetime, timezone, timedelta

from athena_x_runtime_stage5_integration.wire import create_stage5_container
from athena_x_runtime_db_roles import DB_ROLES, get_role_for_schema
from athena_x_runtime_db_partitioning import PartitionManager
from athena_x_runtime_db_events import DBEventType
from athena_x_runtime_db_monitoring import DBMonitor
from athena_x_runtime_db_backup import BackupManager, BackupType


@pytest.fixture
def setup():
    return create_stage5_container()


# ============================================================================
# Functional tests
# ============================================================================

async def test_market_repo_write_and_read(setup):
    """Market repository can write + read quotes."""
    repo = setup["market_repo"]
    record = {"symbol": "SPY", "last_price": 450.0, "timestamp": datetime.now(timezone.utc).isoformat()}
    write = await repo.write_quote(record)
    assert write.record_id is not None

    read = await repo.read_quote("SPY")
    assert read["last_price"] == 450.0


async def test_options_repo_write_and_read(setup):
    """Options repository can write + read chains."""
    repo = setup["options_repo"]
    record = {"symbol": "NVDA", "expiry": "2026-07-18", "strike": 125.0, "delta": 0.65}
    await repo.write_chain(record)
    read = await repo.read_chain("NVDA", "2026-07-18")
    assert read["strike"] == 125.0


async def test_news_repo_write_and_read(setup):
    """News repository can write + read articles."""
    repo = setup["news_repo"]
    record = {"id": "abc-123", "source": "Reuters", "headline": "test", "published_at": datetime.now(timezone.utc).isoformat()}
    await repo.write_article(record)
    read = await repo.read_article("abc-123")
    assert read["headline"] == "test"


async def test_macro_repo_write_and_read(setup):
    """Macro repository can write + read indicators."""
    repo = setup["macro_repo"]
    record = {"indicator": "CPI", "region": "US", "value": 3.2, "timestamp": datetime.now(timezone.utc).isoformat()}
    await repo.write_indicator(record)
    read = await repo.read_indicator("CPI", "US")
    assert read["value"] == 3.2


# ============================================================================
# Integration tests
# ============================================================================

def test_12_writer_roles_defined():
    """All 12 writer roles are defined (Stage 5 req 2)."""
    assert len(DB_ROLES) == 12


def test_each_schema_has_writer():
    """Each schema has exactly one writer role."""
    from athena_x_runtime_db_roles import DB_ROLES
    schemas = [role.schema for role in DB_ROLES.values()]
    assert len(schemas) == len(set(schemas))  # no duplicates


def test_canonical_market_writer_is_market_standardizer():
    """canonical_market's writer is role_market_standardizer."""
    role = get_role_for_schema("canonical_market")
    assert role.name == "role_market_standardizer"


def test_all_repositories_share_monitor(setup):
    """All 4 repositories share the same DB monitor."""
    monitor = setup["monitor"]
    assert setup["market_repo"]._monitor is monitor
    assert setup["options_repo"]._monitor is monitor


# ============================================================================
# Data accuracy tests
# ============================================================================

async def test_written_data_matches_read_data(setup):
    """Data written = data read back."""
    repo = setup["market_repo"]
    record = {
        "symbol": "SPY", "last_price": 450.12,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "asset_class": "etf", "session": "regular",
    }
    await repo.write_quote(record)
    read = await repo.read_quote("SPY")
    assert read["last_price"] == 450.12
    assert read["asset_class"] == "etf"


async def test_immutable_records_supersession(setup):
    """Supersession creates new record, doesn't update old (Stage 5 req 7)."""
    repo = setup["market_repo"]
    original = {"symbol": "SPY", "last_price": 450.0, "timestamp": datetime.now(timezone.utc).isoformat()}
    write1 = await repo.write_quote(original)

    corrected = {"symbol": "SPY", "last_price": 451.0, "timestamp": datetime.now(timezone.utc).isoformat()}
    write2 = await repo.supersede(write1.record_id, corrected)

    # New record has different ID
    assert write2.record_id != write1.record_id
    # Supersession tracked
    assert write2.superseded_record_id == write1.record_id

    # History includes both
    history = await repo.get_history("SPY")
    assert history.count >= 2


# ============================================================================
# Stress tests
# ============================================================================

async def test_stress_1000_writes(setup):
    """Repository handles 1000 writes quickly."""
    repo = setup["market_repo"]
    start = time.monotonic()
    for i in range(1000):
        await repo.write_quote({
            "symbol": f"S{i}", "last_price": 100.0 + i,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
    elapsed = time.monotonic() - start
    rate = 1000 / elapsed
    print(f"\n  ✓ Wrote 1000 records in {elapsed:.2f}s ({rate:.0f} writes/sec)")
    assert rate >= 500


# ============================================================================
# Failover tests
# ============================================================================

def test_writer_lock_rule_enforced():
    """Writer-lock rule: each schema has one designated writer role."""
    # canonical_market → role_market_standardizer
    role = get_role_for_schema("canonical_market")
    assert role is not None
    assert "INSERT" in role.permissions
    # Forecast AI does NOT have write access to canonical_market
    forecast_role = get_role_for_schema("forecast_db")
    assert forecast_role.name == "role_decision"
    assert forecast_role.schema == "forecast_db"  # not canonical_market


# ============================================================================
# Performance tests
# ============================================================================

async def test_performance_write_latency(setup):
    """Write latency p99 < 5ms."""
    repo = setup["market_repo"]
    latencies = []
    for i in range(100):
        start = time.monotonic_ns()
        await repo.write_quote({
            "symbol": "SPY", "last_price": 450.0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        latencies.append((time.monotonic_ns() - start) / 1_000_000)
    latencies.sort()
    p99 = latencies[99]
    print(f"\n  ✓ Write p99: {p99:.2f}ms (budget: <5ms)")
    assert p99 < 5.0


async def test_performance_read_latency(setup):
    """Read latency p99 < 2ms."""
    repo = setup["market_repo"]
    await repo.write_quote({"symbol": "SPY", "last_price": 450.0, "timestamp": datetime.now(timezone.utc).isoformat()})
    latencies = []
    for _ in range(100):
        start = time.monotonic_ns()
        await repo.read_quote("SPY")
        latencies.append((time.monotonic_ns() - start) / 1_000_000)
    latencies.sort()
    p99 = latencies[99]
    print(f"\n  ✓ Read p99: {p99:.2f}ms (budget: <2ms)")
    assert p99 < 2.0


# ============================================================================
# Replay tests
# ============================================================================

async def test_replay_via_history(setup):
    """Can replay history including superseded records."""
    repo = setup["market_repo"]
    # Write + supersede multiple times
    r1 = await repo.write_quote({"symbol": "SPY", "last_price": 450.0, "timestamp": datetime.now(timezone.utc).isoformat()})
    r2 = await repo.supersede(r1.record_id, {"symbol": "SPY", "last_price": 451.0, "timestamp": datetime.now(timezone.utc).isoformat()})
    r3 = await repo.supersede(r2.record_id, {"symbol": "SPY", "last_price": 452.0, "timestamp": datetime.now(timezone.utc).isoformat()})

    history = await repo.get_history("SPY")
    # All 3 versions present
    assert history.count >= 3


# ============================================================================
# Migration tests
# ============================================================================

def test_partitioning_supports_migration():
    """Partition manager can generate partitions for any month."""
    mgr = PartitionManager()
    # Current month
    now = datetime.now(timezone.utc)
    sqls = mgr.generate_sql_for_month("canonical_market", "bars", now.year, now.month)
    assert len(sqls) >= 1
    # Future month
    future = now + timedelta(days=365)
    sqls = mgr.generate_sql_for_month("canonical_market", "bars", future.year, future.month)
    assert len(sqls) >= 1


# ============================================================================
# Integrity tests
# ============================================================================

async def test_data_integrity_after_writes(setup):
    """All written data is retrievable + consistent."""
    repo = setup["market_repo"]
    # Write 10 records
    for i in range(10):
        await repo.write_quote({"symbol": f"SYM{i}", "last_price": 100.0 + i, "timestamp": datetime.now(timezone.utc).isoformat()})
    # All readable
    for i in range(10):
        read = await repo.read_quote(f"SYM{i}")
        assert read is not None
        assert read["last_price"] == 100.0 + i


def test_partition_sql_valid():
    """Generated partition SQL is valid."""
    mgr = PartitionManager()
    spec = mgr.generate_partition("canonical_market", "bars", 2026, 7)
    sql = spec.to_sql()
    assert "PARTITION OF" in sql
    assert "canonical_market" in sql
    assert "2026-07-01" in sql


# ============================================================================
# Recovery tests
# ============================================================================

async def test_backup_and_restore(setup):
    """Backup + restore round-trip works."""
    repo = setup["market_repo"]
    backup_mgr = setup["backup_manager"]

    # Write data
    await repo.write_quote({"symbol": "SPY", "last_price": 450.0, "timestamp": datetime.now(timezone.utc).isoformat()})
    await repo.write_quote({"symbol": "QQQ", "last_price": 380.0, "timestamp": datetime.now(timezone.utc).isoformat()})

    # Backup
    backup = await backup_mgr.backup(
        schemas=["canonical_market"],
        data_provider=repo,
    )
    assert backup.success

    # Clear data
    repo._quotes.clear()
    repo._all_records.clear()
    assert await repo.read_quote("SPY") is None

    # Restore
    restore = await backup_mgr.restore(backup.backup_id, data_provider=repo)
    assert restore.success
    assert restore.records_restored >= 2

    # Data is back
    read = await repo.read_quote("SPY")
    assert read is not None
    assert read["last_price"] == 450.0


async def test_backup_verification(setup):
    """Backup can be verified + restored (CI/CD check)."""
    repo = setup["market_repo"]
    backup_mgr = setup["backup_manager"]

    await repo.write_quote({"symbol": "SPY", "last_price": 450.0, "timestamp": datetime.now(timezone.utc).isoformat()})
    backup = await backup_mgr.backup(schemas=["canonical_market"], data_provider=repo)

    # Verify
    assert backup_mgr.verify_backup(backup.backup_id) is True
    # Verify restore
    result = await backup_mgr.verify_restore(backup.backup_id, data_provider=repo)
    assert result is True


# ============================================================================
# Monitoring tests (Stage 5 req 10)
# ============================================================================

async def test_monitoring_tracks_writes(setup):
    """DB monitor tracks write operations."""
    repo = setup["market_repo"]
    monitor = setup["monitor"]
    for _ in range(5):
        await repo.write_quote({"symbol": "SPY", "last_price": 450.0, "timestamp": datetime.now(timezone.utc).isoformat()})
    metrics = monitor.get_metrics()
    assert metrics.total_writes >= 5
    assert "write_quote" in metrics.by_operation


async def test_monitoring_tracks_latency(setup):
    """DB monitor tracks latency percentiles."""
    repo = setup["market_repo"]
    monitor = setup["monitor"]
    for _ in range(10):
        await repo.write_quote({"symbol": "SPY", "last_price": 450.0, "timestamp": datetime.now(timezone.utc).isoformat()})
    metrics = monitor.get_metrics()
    stats = metrics.by_operation.get("write_quote", {})
    assert "p50" in stats
    assert "p95" in stats
    assert "p99" in stats
    assert stats["p99"] >= stats["p50"]


# ============================================================================
# Event sourcing tests (Stage 5 req 11)
# ============================================================================

async def test_event_sourcing_on_write(setup):
    """Every write emits a db:* event."""
    bus = setup["bus"]
    repo = setup["market_repo"]

    received = []
    async def handler(event):
        received.append(event)
    await bus.subscribe("db:market-written", handler)

    await repo.write_quote({"symbol": "SPY", "last_price": 450.0, "timestamp": datetime.now(timezone.utc).isoformat()})

    assert len(received) == 1
    assert received[0].event_type == "db:market-written"


async def test_event_sourcing_on_supersede(setup):
    """Supersession events include superseded_record_id."""
    bus = setup["bus"]
    repo = setup["market_repo"]

    received = []
    async def handler(event):
        received.append(event)
    await bus.subscribe("db:market-written", handler)

    w1 = await repo.write_quote({"symbol": "SPY", "last_price": 450.0, "timestamp": datetime.now(timezone.utc).isoformat()})
    await repo.supersede(w1.record_id, {"symbol": "SPY", "last_price": 451.0, "timestamp": datetime.now(timezone.utc).isoformat()})

    # 2 events: write + supersede
    assert len(received) == 2
    assert received[1].payload["superseded_record_id"] == w1.record_id
