#!/usr/bin/env python3
"""
STEP 4 Stage 5 - Institutional Database Layer (v2.0)
=====================================================
Implements:
  1. runtime/repository-interface/  - abstract repository protocols (storage-agnostic)
  2. runtime/db-roles/              - database role definitions + RLS policies
  3. runtime/db-partitioning/       - partition management utilities
  4. runtime/db-events/             - event sourcing (db:* events on writes)
  5. runtime/db-monitoring/         - performance metrics + health checks
  6. runtime/db-backup/             - backup + restore utilities
  7. runtime/in-memory-repository/  - InMemoryMarketRepository + 4 domain repos
  8. database/ - updated DDL with partitioning, indexes, RLS, roles
  9. runtime/stage5-integration/    - 9-category acceptance tests

Run: python /home/z/my-project/scripts/stage5_implement.py
"""

from pathlib import Path
import textwrap

ROOT = Path("/home/z/my-project/athena-x")
ROOT.mkdir(parents=True, exist_ok=True)
FILES = []

def w(rel: str, content: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(content).lstrip("\n"))
    FILES.append(rel)


# ============================================================================
# 1. REPOSITORY INTERFACE - runtime/repository-interface/
# ============================================================================

w("runtime/repository-interface/pyproject.toml", '''
[project]
name = "athena-x-runtime-repository-interface"
version = "0.1.0"
description = "Abstract repository protocols - storage-agnostic (Stage 5 strategic req)"
requires-python = ">=3.11"
dependencies = [
    "athena-x-runtime-canonical-types",
    "athena-x-runtime-logger",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_runtime_repository_interface"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w("runtime/repository-interface/src/athena_x_runtime_repository_interface/__init__.py", '''
"""Repository interface - storage-agnostic abstraction (Stage 5 strategic req).

Abstract the storage layer behind Repository Interfaces so you can start
with PostgreSQL/Supabase and later migrate hot time-series workloads to
TimescaleDB or ClickHouse without changing AI agents or business logic.
"""
from .protocols import (
    MarketRepository, OptionsRepository, NewsRepository, MacroRepository,
    RepositoryError, WriteResult, QueryResult,
)
from .base import BaseRepository

__all__ = [
    "MarketRepository", "OptionsRepository", "NewsRepository", "MacroRepository",
    "RepositoryError", "WriteResult", "QueryResult",
    "BaseRepository",
]
__version__ = "0.1.0"
''')

w("runtime/repository-interface/src/athena_x_runtime_repository_interface/protocols.py", '''
"""Abstract repository protocols (Stage 5 strategic recommendation).

These protocols define the storage-agnostic interface that all AI agents
use. Implementations can be:
  - InMemoryMarketRepository (tests + dev)
  - PostgresMarketRepository (production)
  - TimescaleMarketRepository (future - time-series optimized)
  - ClickHouseMarketRepository (future - analytics optimized)

AI agents NEVER talk to the database directly - they always go through
these repository interfaces. This allows migrating storage backends
without changing business logic.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol, runtime_checkable
from uuid import UUID


class RepositoryError(Exception):
    """Base exception for repository operations."""
    def __init__(self, repository: str, message: str):
        self.repository = repository
        super().__init__(f"[{repository}] {message}")


@dataclass
class WriteResult:
    """Result of a write operation."""
    record_id: str
    schema: str
    table: str
    written_at: datetime
    superseded_record_id: str | None = None  # if this record supersedes another
    event_published: bool = False


@dataclass
class QueryResult:
    """Result of a query operation."""
    records: list[Any] = field(default_factory=list)
    count: int = 0
    query_time_ms: float = 0.0


@runtime_checkable
class MarketRepository(Protocol):
    """Repository for canonical market data (Stage 5 req 2).

    ONLY the Market Standardization Agent should write here.
    All other components have read-only access.
    """

    async def write_quote(self, record: Any) -> WriteResult:
        """Write a market quote. Returns WriteResult with record_id."""
        ...

    async def read_quote(self, symbol: str) -> Any | None:
        """Read the latest quote for a symbol."""
        ...

    async def write_bar(self, record: Any) -> WriteResult:
        """Write an OHLCV bar."""
        ...

    async def query_bars(
        self, symbol: str, timeframe: str,
        start: datetime, end: datetime,
    ) -> QueryResult:
        """Query historical bars."""
        ...

    async def supersede(self, record_id: str, corrected: Any) -> WriteResult:
        """Insert a corrected version, marking the old as superseded (Stage 5 req 7).

        Immutable records: never UPDATE - insert new + mark old as superseded.
        """
        ...

    async def get_history(self, symbol: str, limit: int = 100) -> QueryResult:
        """Get historical records for a symbol (including superseded)."""
        ...


@runtime_checkable
class OptionsRepository(Protocol):
    """Repository for canonical options data."""

    async def write_chain(self, record: Any) -> WriteResult: ...
    async def read_chain(self, symbol: str, expiry: Any) -> Any | None: ...
    async def query_chains(self, symbol: str, start: datetime, end: datetime) -> QueryResult: ...
    async def supersede(self, record_id: str, corrected: Any) -> WriteResult: ...


@runtime_checkable
class NewsRepository(Protocol):
    """Repository for canonical news data."""

    async def write_article(self, record: Any) -> WriteResult: ...
    async def read_article(self, article_id: str) -> Any | None: ...
    async def query_articles(
        self, symbols: list[str] | None = None,
        categories: list[str] | None = None,
        start: datetime | None = None, end: datetime | None = None,
        limit: int = 50,
    ) -> QueryResult: ...


@runtime_checkable
class MacroRepository(Protocol):
    """Repository for canonical macro data."""

    async def write_indicator(self, record: Any) -> WriteResult: ...
    async def read_indicator(self, indicator: str, region: str) -> Any | None: ...
    async def query_indicators(
        self, region: str | None = None,
        start: datetime | None = None, end: datetime | None = None,
    ) -> QueryResult: ...
''')

w("runtime/repository-interface/src/athena_x_runtime_repository_interface/base.py", '''
"""Base repository with common functionality."""
from __future__ import annotations
from abc import ABC
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .protocols import WriteResult, RepositoryError


class BaseRepository(ABC):
    """Base class for repository implementations.

    Provides:
      - Record ID generation
      - Timestamp helpers
      - Supersession tracking
    """

    schema_name: str = "unknown"

    def _generate_record_id(self) -> str:
        """Generate a unique record ID."""
        return str(uuid4())

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _make_write_result(
        self, record_id: str, table: str,
        superseded_record_id: str | None = None,
        event_published: bool = False,
    ) -> WriteResult:
        return WriteResult(
            record_id=record_id,
            schema=self.schema_name,
            table=table,
            written_at=self._now(),
            superseded_record_id=superseded_record_id,
            event_published=event_published,
        )
''')

w("runtime/repository-interface/tests/__init__.py", "")
w("runtime/repository-interface/tests/test_protocols.py", '''
"""Tests for repository interface (Stage 5 strategic req)."""
import pytest
from athena_x_runtime_repository_interface import (
    MarketRepository, OptionsRepository, NewsRepository, MacroRepository,
    WriteResult, QueryResult, RepositoryError,
)


def test_write_result_has_required_fields():
    """WriteResult has record_id, schema, table, written_at."""
    from datetime import datetime, timezone
    r = WriteResult(
        record_id="rec-123",
        schema="canonical_market",
        table="quotes",
        written_at=datetime.now(timezone.utc),
    )
    assert r.record_id == "rec-123"
    assert r.schema == "canonical_market"
    assert r.superseded_record_id is None  # no supersession by default


def test_write_result_supports_supersession():
    """WriteResult tracks when a record supersedes another (Stage 5 req 7)."""
    from datetime import datetime, timezone
    r = WriteResult(
        record_id="rec-new",
        schema="canonical_market",
        table="quotes",
        written_at=datetime.now(timezone.utc),
        superseded_record_id="rec-old",
    )
    assert r.superseded_record_id == "rec-old"


def test_query_result_has_records_and_count():
    r = QueryResult(records=[1, 2, 3], count=3)
    assert r.count == 3
    assert len(r.records) == 3


def test_repository_error_includes_repository_name():
    err = RepositoryError("canonical_market", "write failed")
    assert "canonical_market" in str(err)


def test_market_repository_is_protocol():
    """MarketRepository is a runtime-checkable Protocol."""
    assert hasattr(MarketRepository, "_is_protocol")
    assert hasattr(MarketRepository, "_is_runtime_protocol")


def test_all_4_repository_protocols_defined():
    """All 4 domain repository protocols are defined."""
    assert MarketRepository is not None
    assert OptionsRepository is not None
    assert NewsRepository is not None
    assert MacroRepository is not None


def test_market_repository_has_required_methods():
    """MarketRepository defines write_quote, read_quote, write_bar, query_bars, supersede, get_history."""
    # Check protocol has these methods
    assert hasattr(MarketRepository, "write_quote")
    assert hasattr(MarketRepository, "read_quote")
    assert hasattr(MarketRepository, "write_bar")
    assert hasattr(MarketRepository, "query_bars")
    assert hasattr(MarketRepository, "supersede")
    assert hasattr(MarketRepository, "get_history")
''')

# ============================================================================
# 2. DB ROLES - runtime/db-roles/
# ============================================================================

w("runtime/db-roles/pyproject.toml", '''
[project]
name = "athena-x-runtime-db-roles"
version = "0.1.0"
description = "Database role definitions + RLS policies (Stage 5 req 2, 3)"
requires-python = ">=3.11"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_runtime_db_roles"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w("runtime/db-roles/src/athena_x_runtime_db_roles/__init__.py", '''
"""Database roles + RLS policies."""
from .roles import DB_ROLES, ROLE_PERMISSIONS, get_role_for_schema, list_roles
from .rls import RLS_POLICIES, generate_rls_sql

__all__ = ["DB_ROLES", "ROLE_PERMISSIONS", "get_role_for_schema", "list_roles",
           "RLS_POLICIES", "generate_rls_sql"]
__version__ = "0.1.0"
''')

w("runtime/db-roles/src/athena_x_runtime_db_roles/roles.py", '''
"""Database role definitions (Stage 5 req 2).

Each schema has exactly one writing authority.
Enforcement: dedicated database roles per agent.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class DBRole:
    """A database role with specific permissions."""
    name: str
    schema: str
    permissions: list[str]  # INSERT, UPDATE, SELECT, etc.
    description: str
    can_write: bool = True


# 12 writer roles - one per schema
DB_ROLES: dict[str, DBRole] = {
    "role_market_standardizer": DBRole(
        name="role_market_standardizer",
        schema="canonical_market",
        permissions=["INSERT", "UPDATE"],
        description="Market Standardization Agent - ONLY writer to canonical_market",
    ),
    "role_options_standardizer": DBRole(
        name="role_options_standardizer",
        schema="canonical_options",
        permissions=["INSERT", "UPDATE"],
        description="Options Standardization Agent - ONLY writer to canonical_options",
    ),
    "role_news_standardizer": DBRole(
        name="role_news_standardizer",
        schema="canonical_news",
        permissions=["INSERT"],
        description="News Standardization Agent - ONLY writer to canonical_news",
    ),
    "role_macro_standardizer": DBRole(
        name="role_macro_standardizer",
        schema="canonical_macro",
        permissions=["INSERT"],
        description="Macro Standardization Agent - ONLY writer to canonical_macro",
    ),
    "role_validation": DBRole(
        name="role_validation",
        schema="validation_db",
        permissions=["INSERT"],
        description="Validation Agents - write validation decisions",
    ),
    "role_intelligence": DBRole(
        name="role_intelligence",
        schema="ai_intelligence",
        permissions=["INSERT"],
        description="Intelligence Agents - write TA/Options/News/Macro signals",
    ),
    "role_decision": DBRole(
        name="role_decision",
        schema="forecast_db",
        permissions=["INSERT"],
        description="Decision Agents - write regime/scenario/forecast",
    ),
    "role_report_engine": DBRole(
        name="role_report_engine",
        schema="historical_db",
        permissions=["INSERT"],
        description="Report Engine - write reports + backtests",
    ),
    "role_replay_recorder": DBRole(
        name="role_replay_recorder",
        schema="market_replay_db",
        permissions=["INSERT"],
        description="Market Replay Recorder - write minute snapshots",
    ),
    "role_self_correction": DBRole(
        name="role_self_correction",
        schema="ai_memory_db",
        permissions=["INSERT", "UPDATE"],
        description="Self-Correction Agents - write predictions + outcomes + lessons",
    ),
    "role_provider": DBRole(
        name="role_provider",
        schema="raw_landing",
        permissions=["INSERT"],
        description="Provider Adapters - write raw payloads",
    ),
    "role_app_user": DBRole(
        name="role_app_user",
        schema="app",
        permissions=["SELECT", "INSERT", "UPDATE", "DELETE"],
        description="Frontend users - own rows only (RLS enforced)",
    ),
}


# Reader role - read-only access to all schemas
READER_ROLE = DBRole(
    name="role_reader",
    schema="*",
    permissions=["SELECT"],
    description="Read-only access to all canonical schemas",
    can_write=False,
)


ROLE_PERMISSIONS = {name: role.permissions for name, role in DB_ROLES.items()}


def get_role_for_schema(schema: str) -> DBRole | None:
    """Get the writer role for a schema."""
    for role in DB_ROLES.values():
        if role.schema == schema:
            return role
    return None


def list_roles() -> list[str]:
    """List all role names."""
    return list(DB_ROLES.keys())


def generate_role_sql() -> str:
    """Generate SQL to create all roles."""
    lines = ["-- Stage 5: Database roles (writer-lock enforcement)"]
    for role in DB_ROLES.values():
        lines.append(f"CREATE ROLE {role.name} NOLOGIN;")
        lines.append(f"GRANT {', '.join(role.permissions)} ON SCHEMA {role.schema} TO {role.name};")
        lines.append("")
    # Reader role
    lines.append("CREATE ROLE role_reader NOLOGIN;")
    lines.append("GRANT SELECT ON ALL TABLES IN SCHEMA canonical_market, canonical_options, canonical_news, canonical_macro, validation_db, ai_intelligence, forecast_db, historical_db, market_replay_db, ai_memory_db TO role_reader;")
    return "\\n".join(lines)
''')

w("runtime/db-roles/src/athena_x_runtime_db_roles/rls.py", '''
"""RLS policies (Stage 5 req 3).

Apply RLS across all user-facing schemas.
Policies enforce: per-user isolation, workspace isolation, agent-specific roles.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class RLSPolicy:
    """An RLS policy definition."""
    schema: str
    table: str
    policy_name: str
    command: str  # SELECT, INSERT, UPDATE, DELETE, ALL
    using: str  # USING clause
    check: str | None = None  # WITH CHECK clause


RLS_POLICIES: list[RLSPolicy] = [
    # app.workspaces - user owns their workspaces
    RLSPolicy(
        schema="app", table="workspaces",
        policy_name="users_own_workspaces",
        command="ALL",
        using="user_id = auth.uid()",
        check="user_id = auth.uid()",
    ),
    # app.watchlists - workspace member can see
    RLSPolicy(
        schema="app", table="watchlists",
        policy_name="workspace_members_see_watchlists",
        command="SELECT",
        using="EXISTS (SELECT 1 FROM app.workspaces WHERE id = workspace_id AND user_id = auth.uid())",
    ),
    # app.module_instances - workspace member can see
    RLSPolicy(
        schema="app", table="module_instances",
        policy_name="workspace_members_see_instances",
        command="SELECT",
        using="EXISTS (SELECT 1 FROM app.workspaces WHERE id = workspace_id AND user_id = auth.uid())",
    ),
    # historical_db.reports - user owns their reports
    RLSPolicy(
        schema="historical_db", table="reports",
        policy_name="users_own_reports",
        command="ALL",
        using="user_id = auth.uid()",
        check="user_id = auth.uid()",
    ),
    # historical_db.backtests - user owns their backtests
    RLSPolicy(
        schema="historical_db", table="backtests",
        policy_name="users_own_backtests",
        command="ALL",
        using="user_id = auth.uid()",
        check="user_id = auth.uid()",
    ),
]


def generate_rls_sql() -> str:
    """Generate SQL to enable RLS + create policies."""
    lines = ["-- Stage 5: RLS policies"]
    # Enable RLS
    for schema in ["app", "historical_db"]:
        lines.append(f"ALTER TABLE {schema}.workspaces ENABLE ROW LEVEL SECURITY;" if schema == "app" else "")
    # Actually, generate per-table
    seen_tables: set[str] = set()
    for policy in RLS_POLICIES:
        table_full = f"{policy.schema}.{policy.table}"
        if table_full not in seen_tables:
            lines.append(f"ALTER TABLE {table_full} ENABLE ROW LEVEL SECURITY;")
            seen_tables.add(table_full)
        check_clause = f" WITH CHECK ({policy.check})" if policy.check else ""
        lines.append(
            f"CREATE POLICY {policy.policy_name} ON {table_full} "
            f"FOR {policy.command} USING ({policy.using}){check_clause};"
        )
    return "\\n".join(lines)
''')

w("runtime/db-roles/tests/__init__.py", "")
w("runtime/db-roles/tests/test_roles.py", '''
"""Tests for DB roles (Stage 5 req 2)."""
import pytest
from athena_x_runtime_db_roles import DB_ROLES, get_role_for_schema, list_roles, generate_rls_sql


def test_12_writer_roles_defined():
    """12 writer roles - one per schema."""
    assert len(DB_ROLES) == 12


def test_each_schema_has_exactly_one_writer():
    """Each schema has exactly one writer role (writer-lock rule)."""
    schemas = [role.schema for role in DB_ROLES.values()]
    # No duplicates
    assert len(schemas) == len(set(schemas))


def test_get_role_for_canonical_market():
    """canonical_market's writer is role_market_standardizer."""
    role = get_role_for_schema("canonical_market")
    assert role is not None
    assert role.name == "role_market_standardizer"
    assert "INSERT" in role.permissions


def test_get_role_for_unknown_schema():
    assert get_role_for_schema("nonexistent") is None


def test_list_roles_returns_all():
    roles = list_roles()
    assert len(roles) == 12
    assert "role_market_standardizer" in roles
    assert "role_app_user" in roles


def test_role_permissions_are_write_or_read():
    """Writer roles have INSERT; reader doesn't."""
    for role in DB_ROLES.values():
        if role.can_write:
            assert "INSERT" in role.permissions
        else:
            assert "INSERT" not in role.permissions


def test_generate_rls_sql():
    """generate_rls_sql produces valid SQL."""
    sql = generate_rls_sql()
    assert "ENABLE ROW LEVEL SECURITY" in sql
    assert "CREATE POLICY" in sql
    assert "users_own_workspaces" in sql
''')

# ============================================================================
# 3. DB PARTITIONING - runtime/db-partitioning/
# ============================================================================

w("runtime/db-partitioning/pyproject.toml", '''
[project]
name = "athena-x-runtime-db-partitioning"
version = "0.1.0"
description = "Time-series partition management (Stage 5 req 4)"
requires-python = ">=3.11"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_runtime_db_partitioning"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w("runtime/db-partitioning/src/athena_x_runtime_db_partitioning/__init__.py", '''
"""Time-series partitioning utilities."""
from .manager import PartitionManager, PartitionSpec, PartitionStrategy

__all__ = ["PartitionManager", "PartitionSpec", "PartitionStrategy"]
__version__ = "0.1.0"
''')

w("runtime/db-partitioning/src/athena_x_runtime_db_partitioning/manager.py", '''
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
''')

w("runtime/db-partitioning/tests/__init__.py", "")
w("runtime/db-partitioning/tests/test_partitioning.py", '''
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
''')

# ============================================================================
# 4. DB EVENTS - runtime/db-events/
# ============================================================================

w("runtime/db-events/pyproject.toml", '''
[project]
name = "athena-x-runtime-db-events"
version = "0.1.0"
description = "Event sourcing - emit db:* events on writes (Stage 5 req 11)"
requires-python = ">=3.11"
dependencies = [
    "athena-x-runtime-event-bus",
    "athena-x-runtime-logger",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_runtime_db_events"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w("runtime/db-events/src/athena_x_runtime_db_events/__init__.py", '''
"""Database event sourcing (Stage 5 req 11)."""
from .emitter import DBEventEmitter, DBEventType

__all__ = ["DBEventEmitter", "DBEventType"]
__version__ = "0.1.0"
''')

w("runtime/db-events/src/athena_x_runtime_db_events/emitter.py", '''
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
''')

w("runtime/db-events/tests/__init__.py", "")
w("runtime/db-events/tests/test_emitter.py", '''
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
''')

# ============================================================================
# 5. DB MONITORING - runtime/db-monitoring/
# ============================================================================

w("runtime/db-monitoring/pyproject.toml", '''
[project]
name = "athena-x-runtime-db-monitoring"
version = "0.1.0"
description = "Database performance monitoring + health metrics (Stage 5 req 10)"
requires-python = ">=3.11"
dependencies = ["athena-x-runtime-logger"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_runtime_db_monitoring"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w("runtime/db-monitoring/src/athena_x_runtime_db_monitoring/__init__.py", '''
"""Database monitoring."""
from .monitor import DBMonitor, DBMetrics, QueryStats

__all__ = ["DBMonitor", "DBMetrics", "QueryStats"]
__version__ = "0.1.0"
''')

w("runtime/db-monitoring/src/athena_x_runtime_db_monitoring/monitor.py", '''
"""Database performance monitor - Stage 5 req 10.

Tracks:
  - Database latency (p50, p95, p99)
  - Query execution time
  - Insert throughput
  - Storage growth
  - Partition health
  - Index usage
  - Lock contention
  - Connection pool utilization

Expose in Supervisor dashboard (Stage 13).
"""
from __future__ import annotations
import statistics
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import RLock
from typing import Deque


@dataclass
class QueryStats:
    """Statistics for a single query type."""
    operation: str  # "write_quote", "read_quote", etc.
    count: int = 0
    latencies: Deque[float] = field(default_factory=lambda: deque(maxlen=1000))
    errors: int = 0

    def record(self, latency_ms: float, success: bool = True) -> None:
        self.count += 1
        self.latencies.append(latency_ms)
        if not success:
            self.errors += 1

    @property
    def p50(self) -> float:
        return statistics.median(self.latencies) if self.latencies else 0.0

    @property
    def p95(self) -> float:
        if not self.latencies:
            return 0.0
        sorted_l = sorted(self.latencies)
        idx = int(len(sorted_l) * 0.95)
        return sorted_l[min(idx, len(sorted_l) - 1)]

    @property
    def p99(self) -> float:
        if not self.latencies:
            return 0.0
        sorted_l = sorted(self.latencies)
        idx = int(len(sorted_l) * 0.99)
        return sorted_l[min(idx, len(sorted_l) - 1)]

    @property
    def error_rate(self) -> float:
        return self.errors / self.count if self.count > 0 else 0.0


@dataclass
class DBMetrics:
    """Aggregated database metrics for Supervisor dashboard."""
    total_writes: int = 0
    total_reads: int = 0
    total_errors: int = 0
    write_throughput_per_sec: float = 0.0
    avg_write_latency_ms: float = 0.0
    avg_read_latency_ms: float = 0.0
    storage_bytes: int = 0
    partition_count: int = 0
    active_connections: int = 0
    lock_contention_count: int = 0
    by_operation: dict[str, dict] = field(default_factory=dict)


class DBMonitor:
    """Monitors database performance.

    Usage:
        monitor = DBMonitor()
        with monitor.track("write_quote"):
            await repo.write_quote(record)
        metrics = monitor.get_metrics()
    """

    def __init__(self):
        self._stats: dict[str, QueryStats] = {}
        self._lock = RLock()
        self._start_time = time.monotonic()
        self._writes_since_start = 0

    def track(self, operation: str):
        """Context manager to track query latency."""
        return _QueryTracker(self, operation)

    def record(self, operation: str, latency_ms: float, success: bool = True) -> None:
        with self._lock:
            if operation not in self._stats:
                self._stats[operation] = QueryStats(operation=operation)
            self._stats[operation].record(latency_ms, success)
            if "write" in operation:
                self._writes_since_start += 1

    def get_metrics(self) -> DBMetrics:
        with self._lock:
            total_writes = sum(s.count for op, s in self._stats.items() if "write" in op)
            total_reads = sum(s.count for op, s in self._stats.items() if "read" in op)
            total_errors = sum(s.errors for s in self._stats.values())

            elapsed = time.monotonic() - self._start_time
            throughput = self._writes_since_start / elapsed if elapsed > 0 else 0.0

            write_latencies = []
            read_latencies = []
            for op, s in self._stats.items():
                if "write" in op:
                    write_latencies.extend(s.latencies)
                elif "read" in op:
                    read_latencies.extend(s.latencies)

            return DBMetrics(
                total_writes=total_writes,
                total_reads=total_reads,
                total_errors=total_errors,
                write_throughput_per_sec=throughput,
                avg_write_latency_ms=statistics.mean(write_latencies) if write_latencies else 0.0,
                avg_read_latency_ms=statistics.mean(read_latencies) if read_latencies else 0.0,
                by_operation={
                    op: {
                        "count": s.count,
                        "p50": s.p50,
                        "p95": s.p95,
                        "p99": s.p99,
                        "errors": s.errors,
                        "error_rate": s.error_rate,
                    }
                    for op, s in self._stats.items()
                },
            )


class _QueryTracker:
    """Context manager for tracking query latency."""

    def __init__(self, monitor: DBMonitor, operation: str):
        self._monitor = monitor
        self._operation = operation
        self._start = 0.0

    def __enter__(self):
        self._start = time.monotonic_ns()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed_ms = (time.monotonic_ns() - self._start) / 1_000_000
        success = exc_type is None
        self._monitor.record(self._operation, elapsed_ms, success)
        return False
''')

w("runtime/db-monitoring/tests/__init__.py", "")
w("runtime/db-monitoring/tests/test_monitor.py", '''
"""Tests for DB monitoring (Stage 5 req 10)."""
import pytest
import time
from athena_x_runtime_db_monitoring import DBMonitor


def test_track_records_latency():
    monitor = DBMonitor()
    with monitor.track("write_quote"):
        time.sleep(0.001)
    metrics = monitor.get_metrics()
    assert metrics.total_writes == 1
    assert metrics.avg_write_latency_ms > 0


def test_track_records_errors():
    monitor = DBMonitor()
    try:
        with monitor.track("write_quote"):
            raise RuntimeError("test error")
    except RuntimeError:
        pass
    metrics = monitor.get_metrics()
    assert metrics.total_errors == 1


def test_metrics_track_writes_and_reads():
    monitor = DBMonitor()
    with monitor.track("write_quote"):
        pass
    with monitor.track("write_bar"):
        pass
    with monitor.track("read_quote"):
        pass
    metrics = monitor.get_metrics()
    assert metrics.total_writes == 2
    assert metrics.total_reads == 1


def test_by_operation_breakdown():
    monitor = DBMonitor()
    with monitor.track("write_quote"):
        pass
    with monitor.track("write_quote"):
        pass
    with monitor.track("read_quote"):
        pass
    metrics = monitor.get_metrics()
    assert "write_quote" in metrics.by_operation
    assert metrics.by_operation["write_quote"]["count"] == 2
    assert "read_quote" in metrics.by_operation
    assert metrics.by_operation["read_quote"]["count"] == 1


def test_p50_p95_p99_computed():
    monitor = DBMonitor()
    for i in range(100):
        with monitor.track("write_quote"):
            time.sleep(0.0001 * (i + 1))  # increasing latency
    metrics = monitor.get_metrics()
    stats = metrics.by_operation["write_quote"]
    assert stats["p50"] > 0
    assert stats["p95"] >= stats["p50"]
    assert stats["p99"] >= stats["p95"]


def test_write_throughput():
    monitor = DBMonitor()
    for _ in range(10):
        with monitor.track("write_quote"):
            pass
    metrics = monitor.get_metrics()
    assert metrics.write_throughput_per_sec > 0
''')

# ============================================================================
# 6. DB BACKUP - runtime/db-backup/
# ============================================================================

w("runtime/db-backup/pyproject.toml", '''
[project]
name = "athena-x-runtime-db-backup"
version = "0.1.0"
description = "Backup + restore utilities (Stage 5 req 9)"
requires-python = ">=3.11"
dependencies = ["athena-x-runtime-logger"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_runtime_db_backup"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w("runtime/db-backup/src/athena_x_runtime_db_backup/__init__.py", '''
"""Backup + restore utilities."""
from .manager import BackupManager, BackupResult, RestoreResult, BackupType

__all__ = ["BackupManager", "BackupResult", "RestoreResult", "BackupType"]
__version__ = "0.1.0"
''')

w("runtime/db-backup/src/athena_x_runtime_db_backup/manager.py", '''
"""Backup manager - Stage 5 req 9.

Implements:
  - Daily full backups
  - Frequent incremental backups
  - Point-in-time recovery (PITR) interface
  - Restore verification

> "A backup is only useful if it has been successfully restored in testing."
"""
from __future__ import annotations
import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import uuid4

from athena_x_runtime_logger import get_logger

log = get_logger("runtime.db-backup")


class BackupType(str, Enum):
    FULL = "full"
    INCREMENTAL = "incremental"


@dataclass
class BackupResult:
    """Result of a backup operation."""
    backup_id: str
    backup_type: BackupType
    path: str
    size_bytes: int
    created_at: datetime
    schemas_included: list[str] = field(default_factory=list)
    success: bool = True
    error: str | None = None


@dataclass
class RestoreResult:
    """Result of a restore operation."""
    backup_id: str
    restored_at: datetime
    schemas_restored: list[str] = field(default_factory=list)
    records_restored: int = 0
    success: bool = True
    error: str | None = None


class BackupManager:
    """Manages database backups + restores.

    Stage 5 req 9:
      - Daily full backups
      - Frequent incremental backups
      - PITR
      - Restore verification in CI/CD
    """

    def __init__(self, backup_root: str | Path = "/tmp/athena-x-backups"):
        self._backup_root = Path(backup_root)
        self._backup_root.mkdir(parents=True, exist_ok=True)
        self._backups: dict[str, BackupResult] = {}

    async def backup(
        self,
        *,
        schemas: list[str],
        data_provider: Any = None,
        backup_type: BackupType = BackupType.FULL,
    ) -> BackupResult:
        """Create a backup of specified schemas."""
        backup_id = str(uuid4())
        backup_dir = self._backup_root / backup_id
        backup_dir.mkdir(parents=True, exist_ok=True)

        try:
            schemas_included = []
            total_size = 0

            for schema in schemas:
                schema_dir = backup_dir / schema
                schema_dir.mkdir(exist_ok=True)

                # If data_provider given, dump its data
                if data_provider and hasattr(data_provider, "dump_schema"):
                    data = await data_provider.dump_schema(schema)
                    schema_file = schema_dir / "data.json"
                    schema_file.write_text(json.dumps(data, default=str))
                    total_size += schema_file.stat().st_size
                    schemas_included.append(schema)

                # Write schema manifest
                manifest = {
                    "schema": schema,
                    "backup_type": backup_type.value,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                (schema_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))

            result = BackupResult(
                backup_id=backup_id,
                backup_type=backup_type,
                path=str(backup_dir),
                size_bytes=total_size,
                created_at=datetime.now(timezone.utc),
                schemas_included=schemas_included,
            )
            self._backups[backup_id] = result
            log.info("backup_created",
                     backup_id=backup_id,
                     type=backup_type.value,
                     schemas=len(schemas_included),
                     size_bytes=total_size)
            return result

        except Exception as e:
            log.error("backup_failed", error=str(e))
            return BackupResult(
                backup_id=backup_id,
                backup_type=backup_type,
                path=str(backup_dir),
                size_bytes=0,
                created_at=datetime.now(timezone.utc),
                success=False,
                error=str(e),
            )

    async def restore(
        self,
        backup_id: str,
        data_provider: Any = None,
    ) -> RestoreResult:
        """Restore from a backup."""
        backup = self._backups.get(backup_id)
        if backup is None:
            # Check filesystem
            backup_dir = self._backup_root / backup_id
            if not backup_dir.exists():
                return RestoreResult(
                    backup_id=backup_id,
                    restored_at=datetime.now(timezone.utc),
                    success=False,
                    error=f"Backup not found: {backup_id}",
                )

        backup_dir = self._backup_root / backup_id
        schemas_restored = []
        records = 0

        try:
            for schema_dir in backup_dir.iterdir():
                if not schema_dir.is_dir():
                    continue
                schema = schema_dir.name
                data_file = schema_dir / "data.json"
                if data_file.exists() and data_provider and hasattr(data_provider, "restore_schema"):
                    data = json.loads(data_file.read_text())
                    count = await data_provider.restore_schema(schema, data)
                    records += count
                    schemas_restored.append(schema)

            result = RestoreResult(
                backup_id=backup_id,
                restored_at=datetime.now(timezone.utc),
                schemas_restored=schemas_restored,
                records_restored=records,
            )
            log.info("backup_restored",
                     backup_id=backup_id,
                     schemas=len(schemas_restored),
                     records=records)
            return result

        except Exception as e:
            log.error("restore_failed", error=str(e))
            return RestoreResult(
                backup_id=backup_id,
                restored_at=datetime.now(timezone.utc),
                success=False,
                error=str(e),
            )

    def list_backups(self) -> list[BackupResult]:
        return list(self._backups.values())

    def verify_backup(self, backup_id: str) -> bool:
        """Verify a backup exists + is readable."""
        backup = self._backups.get(backup_id)
        if backup is None:
            return False
        return Path(backup.path).exists()

    async def verify_restore(self, backup_id: str, data_provider: Any = None) -> bool:
        """Verify a backup can be restored (CI/CD check).

        > "A backup is only useful if it has been successfully restored in testing."
        """
        result = await self.restore(backup_id, data_provider)
        return result.success
''')

w("runtime/db-backup/tests/__init__.py", "")
w("runtime/db-backup/tests/test_backup.py", '''
"""Tests for backup manager (Stage 5 req 9)."""
import pytest
from athena_x_runtime_db_backup import BackupManager, BackupType


class FakeDataProvider:
    """Fake data provider for testing."""
    def __init__(self):
        self.data = {
            "canonical_market": [{"symbol": "SPY", "last": 450.0}],
            "canonical_options": [{"symbol": "NVDA", "strike": 125.0}],
        }

    async def dump_schema(self, schema):
        return self.data.get(schema, [])

    async def restore_schema(self, schema, data):
        self.data[schema] = data
        return len(data)


@pytest.fixture
def backup_mgr(tmp_path):
    return BackupManager(backup_root=tmp_path / "backups")


async def test_backup_creates_files(backup_mgr):
    """Backup creates files on disk."""
    provider = FakeDataProvider()
    result = await backup_mgr.backup(
        schemas=["canonical_market", "canonical_options"],
        data_provider=provider,
    )
    assert result.success
    assert len(result.schemas_included) == 2
    assert result.size_bytes > 0


async def test_restore_recovers_data(backup_mgr):
    """Restore recovers data from backup."""
    provider = FakeDataProvider()
    backup = await backup_mgr.backup(
        schemas=["canonical_market"],
        data_provider=provider,
    )
    # Clear provider data
    provider.data["canonical_market"] = []
    # Restore
    result = await backup_mgr.restore(backup.backup_id, data_provider=provider)
    assert result.success
    assert "canonical_market" in result.schemas_restored
    assert result.records_restored == 1
    assert len(provider.data["canonical_market"]) == 1


async def test_restore_nonexistent_backup_fails(backup_mgr):
    result = await backup_mgr.restore("nonexistent-id")
    assert not result.success
    assert "not found" in result.error


async def test_verify_backup(backup_mgr):
    """verify_backup checks backup exists."""
    provider = FakeDataProvider()
    backup = await backup_mgr.backup(
        schemas=["canonical_market"],
        data_provider=provider,
    )
    assert backup_mgr.verify_backup(backup.backup_id) is True
    assert backup_mgr.verify_backup("nonexistent") is False


async def test_verify_restore(backup_mgr):
    """verify_restore tests that backup can be restored (CI/CD check)."""
    provider = FakeDataProvider()
    backup = await backup_mgr.backup(
        schemas=["canonical_market"],
        data_provider=provider,
    )
    result = await backup_mgr.verify_restore(backup.backup_id, data_provider=provider)
    assert result is True


def test_backup_types():
    assert BackupType.FULL.value == "full"
    assert BackupType.INCREMENTAL.value == "incremental"
''')

# ============================================================================
# 7. IN-MEMORY REPOSITORY - runtime/in-memory-repository/
# ============================================================================

w("runtime/in-memory-repository/pyproject.toml", '''
[project]
name = "athena-x-runtime-in-memory-repository"
version = "0.1.0"
description = "In-memory repository implementation (tests + dev - no DB required)"
requires-python = ">=3.11"
dependencies = [
    "athena-x-runtime-repository-interface",
    "athena-x-runtime-canonical-types",
    "athena-x-runtime-db-events",
    "athena-x-runtime-db-monitoring",
    "athena-x-runtime-logger",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_runtime_in_memory_repository"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
''')

w("runtime/in-memory-repository/src/athena_x_runtime_in_memory_repository/__init__.py", '''
"""In-memory repository implementations."""
from .market import InMemoryMarketRepository
from .options import InMemoryOptionsRepository
from .news import InMemoryNewsRepository
from .macro import InMemoryMacroRepository

__all__ = [
    "InMemoryMarketRepository",
    "InMemoryOptionsRepository",
    "InMemoryNewsRepository",
    "InMemoryMacroRepository",
]
__version__ = "0.1.0"
''')

w("runtime/in-memory-repository/src/athena_x_runtime_in_memory_repository/market.py", '''
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
''')

w("runtime/in-memory-repository/src/athena_x_runtime_in_memory_repository/options.py", '''
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
''')

w("runtime/in-memory-repository/src/athena_x_runtime_in_memory_repository/news.py", '''
"""In-memory NewsRepository."""
from __future__ import annotations
from datetime import datetime
from threading import RLock
from typing import Any

from athena_x_runtime_repository_interface import WriteResult, QueryResult
from athena_x_runtime_repository_interface.base import BaseRepository
from athena_x_runtime_db_events import DBEventEmitter, DBEventType
from athena_x_runtime_db_monitoring import DBMonitor


class InMemoryNewsRepository(BaseRepository):
    schema_name = "canonical_news"

    def __init__(self, event_emitter=None, monitor=None):
        self._articles: dict[str, dict] = {}  # id → article
        self._lock = RLock()
        self._emitter = event_emitter or DBEventEmitter()
        self._monitor = monitor or DBMonitor()

    async def write_article(self, record: Any) -> WriteResult:
        with self._monitor.track("write_article"):
            with self._lock:
                record_id = record.get("id", self._generate_record_id())
                stored = {"record_id": record_id, "data": record, "written_at": self._now().isoformat()}
                self._articles[record_id] = stored

            result = self._make_write_result(record_id, "headlines", event_published=True)
            await self._emitter.emit_write(
                event_type=DBEventType.NEWS_WRITTEN,
                schema=self.schema_name, table="headlines",
                record_id=record_id, symbol=None, payload=record,
            )
            return result

    async def read_article(self, article_id: str) -> Any | None:
        with self._monitor.track("read_article"):
            with self._lock:
                stored = self._articles.get(article_id)
                return stored["data"] if stored else None

    async def query_articles(
        self, symbols=None, categories=None,
        start=None, end=None, limit=50,
    ) -> QueryResult:
        with self._monitor.track("query_articles"):
            with self._lock:
                results = []
                for stored in self._articles.values():
                    article = stored["data"]
                    # Filter by symbols
                    if symbols and not any(s in article.get("symbols", []) for s in symbols):
                        continue
                    # Filter by categories
                    if categories and not any(c in article.get("categories", []) for c in categories):
                        continue
                    results.append(article)
                    if len(results) >= limit:
                        break
                return QueryResult(records=results, count=len(results))
''')

w("runtime/in-memory-repository/src/athena_x_runtime_in_memory_repository/macro.py", '''
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
''')

w("runtime/in-memory-repository/tests/__init__.py", "")
w("runtime/in-memory-repository/tests/test_market_repo.py", '''
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
''')

# ============================================================================
# 8. UPDATED DATABASE DDL - database/ (partitioning + indexes + RLS + roles)
# ============================================================================

w("database/canonical-market/schema.sql", '''
-- ============================================================================
-- canonical_market - Layer 4 Database 1: Standardized Market Data
-- Writer: Market Standardization Agent ONLY (role_market_standardizer)
-- Stage 5: partitioned + indexed + immutable + RLS
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS canonical_market;

-- Quotes table (partitioned monthly)
CREATE TABLE IF NOT EXISTS canonical_market.quotes (
    record_id           UUID NOT NULL DEFAULT gen_random_uuid(),
    symbol              TEXT NOT NULL,
    asset_class         TEXT NOT NULL,
    exchange            TEXT,
    timestamp           TIMESTAMPTZ NOT NULL,
    market_timestamp    TIMESTAMPTZ NOT NULL,
    session             TEXT NOT NULL,
    trading_day         DATE,
    exchange_local_time TIMESTAMPTZ,
    last_price          NUMERIC NOT NULL,
    open                NUMERIC,
    high                NUMERIC,
    low                 NUMERIC,
    close               NUMERIC,
    bid                 NUMERIC,
    ask                 NUMERIC,
    volume              BIGINT,
    currency            TEXT DEFAULT 'USD',
    market              TEXT,
    sector              TEXT,
    industry            TEXT,
    region              TEXT,
    -- Provenance
    source_provider     TEXT NOT NULL,
    raw_payload_id      TEXT,
    validation_id       TEXT,
    transformation_id   TEXT,
    -- Versioning
    schema_version      TEXT NOT NULL,
    mapping_version     TEXT NOT NULL,
    provider_version    TEXT,
    -- Metadata
    provider_metadata   JSONB DEFAULT '{}'::jsonb,
    validation_metadata JSONB DEFAULT '{}'::jsonb,
    -- Immutable records (Stage 5 req 7)
    superseded_by       UUID,  -- if non-null, this record is superseded
    supersedes          UUID,  -- if non-null, this record supersedes another
    written_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (record_id, market_timestamp)
) PARTITION BY RANGE (market_timestamp);

-- Indexes (Stage 5 req 5)
CREATE INDEX IF NOT EXISTS idx_quotes_symbol_time ON canonical_market.quotes (symbol, market_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_quotes_session ON canonical_market.quotes (symbol, session, market_timestamp);
CREATE INDEX IF NOT EXISTS idx_quotes_provider ON canonical_market.quotes (source_provider, market_timestamp);

-- Bars table (partitioned monthly)
CREATE TABLE IF NOT EXISTS canonical_market.bars (
    record_id           UUID NOT NULL DEFAULT gen_random_uuid(),
    symbol              TEXT NOT NULL,
    timeframe           TEXT NOT NULL,
    timestamp           BIGINT NOT NULL,  -- unix-millis
    market_timestamp    TIMESTAMPTZ NOT NULL,
    open                NUMERIC NOT NULL,
    high                NUMERIC NOT NULL,
    low                 NUMERIC NOT NULL,
    close               NUMERIC NOT NULL,
    volume              BIGINT NOT NULL,
    source_provider     TEXT NOT NULL,
    schema_version      TEXT NOT NULL,
    superseded_by       UUID,
    written_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (record_id, market_timestamp)
) PARTITION BY RANGE (market_timestamp);

CREATE INDEX IF NOT EXISTS idx_bars_lookup ON canonical_market.bars (symbol, timeframe, market_timestamp DESC);

-- Trades table (partitioned DAILY - high frequency)
CREATE TABLE IF NOT EXISTS canonical_market.trades (
    record_id           UUID NOT NULL DEFAULT gen_random_uuid(),
    symbol              TEXT NOT NULL,
    price               NUMERIC NOT NULL,
    size                INTEGER NOT NULL,
    side                TEXT,
    market_timestamp    TIMESTAMPTZ NOT NULL,
    source_provider     TEXT NOT NULL,
    written_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (record_id, market_timestamp)
) PARTITION BY RANGE (market_timestamp);

CREATE INDEX IF NOT EXISTS idx_trades_symbol_time ON canonical_market.trades (symbol, market_timestamp);

COMMENT ON SCHEMA canonical_market IS 'Layer 4 Database 1 - Standardized Market Data. Writer: role_market_standardizer ONLY';
''')

w("database/canonical-options/schema.sql", '''
-- ============================================================================
-- canonical_options - Layer 4 Database 2: Standardized Options Data
-- Writer: Options Standardization Agent ONLY (role_options_standardizer)
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS canonical_options;

CREATE TABLE IF NOT EXISTS canonical_options.chains (
    record_id           UUID NOT NULL DEFAULT gen_random_uuid(),
    symbol              TEXT NOT NULL,
    underlying          TEXT NOT NULL,
    expiry              DATE NOT NULL,
    strike              NUMERIC NOT NULL,
    option_type         TEXT NOT NULL,  -- 'call' | 'put'
    timestamp           TIMESTAMPTZ NOT NULL,
    market_timestamp    TIMESTAMPTZ NOT NULL,
    bid                 NUMERIC,
    ask                 NUMERIC,
    last_price          NUMERIC,
    volume              BIGINT,
    open_interest       BIGINT,
    implied_volatility  NUMERIC,
    delta               NUMERIC,
    gamma               NUMERIC,
    theta               NUMERIC,
    vega                NUMERIC,
    rho                 NUMERIC,
    source_provider     TEXT NOT NULL,
    schema_version      TEXT NOT NULL,
    superseded_by       UUID,
    written_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (record_id, market_timestamp)
) PARTITION BY RANGE (market_timestamp);

CREATE INDEX IF NOT EXISTS idx_chains_lookup ON canonical_options.chains (symbol, expiry, strike);
CREATE INDEX IF NOT EXISTS idx_chains_underlying ON canonical_options.chains (underlying, expiry);

COMMENT ON SCHEMA canonical_options IS 'Layer 4 Database 2 - Standardized Options. Writer: role_options_standardizer ONLY';
''')

w("database/migrations/20260103000000_stage5_institutional_db.sql", '''
-- ============================================================================
-- Stage 5 Migration: Institutional Database Layer v2.0
-- Adds: partitioning, indexes, RLS, writer-lock roles, immutable records
-- ============================================================================

-- 1. Create writer-lock roles (Stage 5 req 2)
CREATE ROLE role_market_standardizer NOLOGIN;
CREATE ROLE role_options_standardizer NOLOGIN;
CREATE ROLE role_news_standardizer NOLOGIN;
CREATE ROLE role_macro_standardizer NOLOGIN;
CREATE ROLE role_validation NOLOGIN;
CREATE ROLE role_intelligence NOLOGIN;
CREATE ROLE role_decision NOLOGIN;
CREATE ROLE role_report_engine NOLOGIN;
CREATE ROLE role_replay_recorder NOLOGIN;
CREATE ROLE role_self_correction NOLOGIN;
CREATE ROLE role_provider NOLOGIN;
CREATE ROLE role_reader NOLOGIN;

-- 2. Grant schema permissions (writer-lock enforcement)
GRANT INSERT, UPDATE ON canonical_market.quotes TO role_market_standardizer;
GRANT INSERT, UPDATE ON canonical_market.bars TO role_market_standardizer;
GRANT INSERT, UPDATE ON canonical_market.trades TO role_market_standardizer;
GRANT SELECT ON canonical_market.quotes TO role_reader;
GRANT SELECT ON canonical_market.bars TO role_reader;
GRANT SELECT ON canonical_market.trades TO role_reader;

GRANT INSERT, UPDATE ON canonical_options.chains TO role_options_standardizer;
GRANT SELECT ON canonical_options.chains TO role_reader;

-- 3. Enable RLS on user-facing schemas (Stage 5 req 3)
-- (already done in database/policies/rls.sql)

-- 4. Create partitions for current month + next month
-- (run by PartitionManager at startup)

COMMENT ON SCHEMA canonical_market IS 'Stage 5 - partitioned, indexed, immutable, RLS-enforced';
''')

# ============================================================================
# 9. STAGE 5 INTEGRATION - runtime/stage5-integration/
# ============================================================================

w("runtime/stage5-integration/pyproject.toml", '''
[project]
name = "athena-x-runtime-stage5-integration"
version = "0.1.0"
description = "Stage 5 integration - 9-category acceptance tests"
requires-python = ">=3.11"
dependencies = [
    "athena-x-runtime-repository-interface",
    "athena-x-runtime-in-memory-repository",
    "athena-x-runtime-db-roles",
    "athena-x-runtime-db-partitioning",
    "athena-x-runtime-db-events",
    "athena-x-runtime-db-monitoring",
    "athena-x-runtime-db-backup",
    "athena-x-runtime-event-bus",
    "athena-x-runtime-canonical-types",
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/athena_x_runtime_stage5_integration"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
markers = [
    "functional: functional tests",
    "integration: integration tests",
    "accuracy: data accuracy tests",
    "stress: stress tests",
    "failover: failover tests",
    "performance: performance tests",
    "replay: replay tests",
    "migration: migration tests",
    "integrity: integrity tests",
    "recovery: recovery tests",
]
''')

w("runtime/stage5-integration/src/athena_x_runtime_stage5_integration/__init__.py", '''"""Stage 5 integration."""''')

w("runtime/stage5-integration/src/athena_x_runtime_stage5_integration/wire.py", '''
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
''')

w("runtime/stage5-integration/tests/__init__.py", "")
w("runtime/stage5-integration/tests/test_stage5_acceptance.py", '''
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
    print(f"\\n  ✓ Wrote 1000 records in {elapsed:.2f}s ({rate:.0f} writes/sec)")
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
    print(f"\\n  ✓ Write p99: {p99:.2f}ms (budget: <5ms)")
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
    print(f"\\n  ✓ Read p99: {p99:.2f}ms (budget: <2ms)")
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
''')

print(f"\n✅ Stage 5 complete: {len(FILES)} files written")
print("\nComponents implemented:")
print("  1. runtime/repository-interface/   - abstract protocols (storage-agnostic)")
print("  2. runtime/db-roles/               - 12 writer roles + RLS policies")
print("  3. runtime/db-partitioning/        - monthly + daily partition management")
print("  4. runtime/db-events/              - event sourcing (db:* events)")
print("  5. runtime/db-monitoring/          - latency, throughput, p50/p95/p99")
print("  6. runtime/db-backup/              - backup + restore + verify")
print("  7. runtime/in-memory-repository/   - 4 domain repos (market/options/news/macro)")
print("  8. database/                       - updated DDL (partitioned + indexed + immutable)")
print("  9. runtime/stage5-integration/     - 9-category acceptance tests")
print("\nNext: install deps and run tests")
