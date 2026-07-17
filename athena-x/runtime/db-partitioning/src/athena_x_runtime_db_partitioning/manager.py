"""Partition manager - Stage 5 req 4.

Time-series partitioning for high-volume tables.

canonical_market.bars
├── 2026
│   ├── 07
│   ├── 08
│   └── 09

For very high-frequency data (ticks), use daily partitions.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum
from typing import Any


class PartitionStrategy(str, Enum):
    MONTHLY = "monthly"
    DAILY = "daily"


@dataclass(frozen=True)
class PartitionSpec:
    """Specification for a partition."""
    schema: str
    table: str
    strategy: PartitionStrategy
    year: int
    month: int
    day: int | None = None  # for daily partitions

    @property
    def partition_name(self) -> str:
        if self.strategy == PartitionStrategy.MONTHLY:
            return f"{self.table}_{self.year}_{self.month:02d}"
        return f"{self.table}_{self.year}_{self.month:02d}_{self.day:02d}"

    @property
    def start_date(self) -> date:
        return date(self.year, self.month, self.day or 1)

    @property
    def end_date(self) -> date:
        if self.strategy == PartitionStrategy.MONTHLY:
            if self.month == 12:
                return date(self.year + 1, 1, 1)
            return date(self.year, self.month + 1, 1)
        return self.start_date + timedelta(days=1)

    def to_sql(self) -> str:
        """Generate CREATE TABLE ... PARTITION OF SQL."""
        return (
            f"CREATE TABLE IF NOT EXISTS {self.schema}.{self.partition_name} "
            f"PARTITION OF {self.schema}.{self.table} "
            f"FOR VALUES FROM ('{self.start_date.isoformat()}') "
            f"TO ('{self.end_date.isoformat()}');"
        )


# Tables that should be partitioned (Stage 5 req 4)
PARTITIONED_TABLES: dict[str, PartitionStrategy] = {
    "canonical_market.quotes": PartitionStrategy.MONTHLY,
    "canonical_market.bars": PartitionStrategy.MONTHLY,
    "canonical_market.trades": PartitionStrategy.DAILY,
    "canonical_options.chains": PartitionStrategy.MONTHLY,
    "raw_landing.provider_payloads": PartitionStrategy.MONTHLY,
    "market_replay_db.minute_snapshots": PartitionStrategy.MONTHLY,
    "ai_memory_db.predictions": PartitionStrategy.MONTHLY,
}


class PartitionManager:
    """Manages time-series partitions."""

    def __init__(self):
        self._specs: dict[str, PartitionStrategy] = dict(PARTITIONED_TABLES)

    def get_strategy(self, schema: str, table: str) -> PartitionStrategy | None:
        key = f"{schema}.{table}"
        return self._specs.get(key)

    def generate_partition(
        self, schema: str, table: str,
        year: int, month: int, day: int | None = None,
    ) -> PartitionSpec:
        """Generate a partition spec for a given date."""
        strategy = self.get_strategy(schema, table)
        if strategy is None:
            raise ValueError(f"Table {schema}.{table} is not configured for partitioning")
        return PartitionSpec(
            schema=schema, table=table, strategy=strategy,
            year=year, month=month, day=day,
        )

    def generate_partitions_for_month(
        self, schema: str, table: str, year: int, month: int,
    ) -> list[PartitionSpec]:
        """Generate all partitions for a month (daily if strategy is DAILY)."""
        strategy = self.get_strategy(schema, table)
        if strategy is None:
            return []
        if strategy == PartitionStrategy.MONTHLY:
            return [self.generate_partition(schema, table, year, month)]
        # Daily - generate all days in month
        partitions = []
        day = 1
        while True:
            try:
                d = date(year, month, day)
            except ValueError:
                break
            partitions.append(self.generate_partition(schema, table, year, month, day))
            day += 1
        return partitions

    def generate_sql_for_month(
        self, schema: str, table: str, year: int, month: int,
    ) -> list[str]:
        """Generate CREATE TABLE SQL for all partitions in a month."""
        return [p.to_sql() for p in self.generate_partitions_for_month(schema, table, year, month)]

    def list_partitioned_tables(self) -> list[str]:
        return list(self._specs.keys())
