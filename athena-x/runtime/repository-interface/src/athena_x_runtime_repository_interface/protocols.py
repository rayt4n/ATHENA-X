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
