"""Tests for partitioning (Stage 5 req 4)."""
import pytest
from athena_x_runtime_db_partitioning import (
    PartitionManager, PartitionSpec, PartitionStrategy,
)


def test_monthly_partition_spec():
    spec = PartitionSpec(
        schema="canonical_market", table="bars",
        strategy=PartitionStrategy.MONTHLY, year=2026, month=7,
    )
    assert spec.partition_name == "bars_2026_07"
    assert str(spec.start_date) == "2026-07-01"
    assert str(spec.end_date) == "2026-08-01"


def test_daily_partition_spec():
    spec = PartitionSpec(
        schema="canonical_market", table="trades",
        strategy=PartitionStrategy.DAILY, year=2026, month=7, day=17,
    )
    assert spec.partition_name == "trades_2026_07_17"
    assert str(spec.start_date) == "2026-07-17"
    assert str(spec.end_date) == "2026-07-18"


def test_partition_sql_generated():
    spec = PartitionSpec(
        schema="canonical_market", table="bars",
        strategy=PartitionStrategy.MONTHLY, year=2026, month=7,
    )
    sql = spec.to_sql()
    assert "PARTITION OF" in sql
    assert "bars_2026_07" in sql
    assert "2026-07-01" in sql
    assert "2026-08-01" in sql


def test_partition_manager_lists_tables():
    mgr = PartitionManager()
    tables = mgr.list_partitioned_tables()
    assert "canonical_market.bars" in tables
    assert "canonical_market.trades" in tables
    assert "raw_landing.provider_payloads" in tables


def test_partition_manager_monthly():
    mgr = PartitionManager()
    specs = mgr.generate_partitions_for_month("canonical_market", "bars", 2026, 7)
    assert len(specs) == 1  # monthly = 1 partition
    assert specs[0].partition_name == "bars_2026_07"


def test_partition_manager_daily():
    """Daily partitioning generates one partition per day."""
    mgr = PartitionManager()
    specs = mgr.generate_partitions_for_month("canonical_market", "trades", 2026, 7)
    assert len(specs) == 31  # July has 31 days
    assert specs[0].partition_name == "trades_2026_07_01"
    assert specs[30].partition_name == "trades_2026_07_31"


def test_partition_sql_for_month():
    mgr = PartitionManager()
    sqls = mgr.generate_sql_for_month("canonical_market", "bars", 2026, 7)
    assert len(sqls) == 1
    assert "PARTITION OF" in sqls[0]


def test_december_partition_end_date():
    """December partition ends on Jan 1 of next year."""
    spec = PartitionSpec(
        schema="canonical_market", table="bars",
        strategy=PartitionStrategy.MONTHLY, year=2026, month=12,
    )
    assert str(spec.end_date) == "2027-01-01"
