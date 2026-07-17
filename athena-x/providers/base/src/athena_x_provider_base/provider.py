"""MarketDataProvider protocol + result types."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Protocol, runtime_checkable

from .types import Quote, Bar, Trade, OptionChain, NewsArticle


@dataclass
class ProviderResult:
    """Wraps a successful provider response with metadata."""
    data: Any  # Quote, Bar, Trade, OptionChain, or NewsArticle
    provider: str
    latency_ms: int
    raw_payload: Any  # original provider response (for archival)
    market_timestamp: datetime


class ProviderError(Exception):
    """Raised when a provider call fails."""
    def __init__(self, provider: str, message: str, status_code: int | None = None):
        self.provider = provider
        self.status_code = status_code
        super().__init__(f"[{provider}] {message}")


@runtime_checkable
class MarketDataProvider(Protocol):
    """Protocol that all provider adapters implement.

    Stage 2 rule: providers ONLY download data. Never calculate.
    """

    name: str
    transport: str
    asset_classes: list[str]

    async def fetch_quote(self, symbol: str) -> ProviderResult:
        """Fetch a real-time quote for a symbol."""
        ...

    async def fetch_bars(
        self,
        symbol: str,
        timeframe: str,
        count: int,
    ) -> list[ProviderResult]:
        """Fetch historical OHLCV bars."""
        ...

    async def fetch_option_chain(
        self,
        symbol: str,
        expiry: date,
    ) -> ProviderResult:
        """Fetch an options chain for a symbol on a specific expiry."""
        ...

    async def fetch_news(
        self,
        symbols: list[str] | None = None,
        categories: list[str] | None = None,
        limit: int = 50,
    ) -> list[ProviderResult]:
        """Fetch news articles."""
        ...

    async def health_check(self) -> dict:
        """Return provider health metrics."""
        ...
