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
