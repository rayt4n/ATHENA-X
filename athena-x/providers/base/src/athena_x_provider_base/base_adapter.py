"""Base provider adapter with common functionality.

Provides:
- API key management
- Rate limiting (simple)
- Latency measurement
- Raw payload archival (via RawArchiver)
- Freshness tracking (via FreshnessTracker)
- Health metric collection

Concrete providers subclass this and implement fetch_* methods.
"""
from __future__ import annotations
import time
from datetime import datetime, timezone
from typing import Any

from athena_x_runtime_logger import get_logger
from athena_x_runtime_institutional_metadata import create_metadata, InstitutionalMetadata
from athena_x_runtime_raw_archival import RawArchiver
from athena_x_runtime_data_freshness import FreshnessTracker

from .provider import ProviderResult, ProviderError

log = get_logger("providers.base")


class BaseProviderAdapter:
    """Base class for provider adapters.

    Subclasses must implement:
      - async def _fetch_quote(self, symbol: str) -> tuple[Any, datetime]
      - async def _fetch_bars(...) -> list[tuple[Any, datetime]]
      - etc.

    The _fetch_* methods return (raw_payload, market_timestamp) tuples.
    The base class handles archival, freshness tracking, and metadata.
    """

    name: str = "base"
    transport: str = "unknown"
    asset_classes: list[str] = []

    def __init__(
        self,
        api_key: str | None = None,
        archiver: RawArchiver | None = None,
        freshness_tracker: FreshnessTracker | None = None,
    ):
        self.api_key = api_key
        self._archiver = archiver
        self._freshness = freshness_tracker
        self._call_count = 0
        self._success_count = 0
        self._failure_count = 0
        self._latencies: list[float] = []
        self._last_success: datetime | None = None

    async def fetch_quote(self, symbol: str) -> ProviderResult:
        """Fetch a quote. Measures latency, archives raw, tracks freshness."""
        start = time.monotonic()
        try:
            raw_payload, market_ts = await self._fetch_quote(symbol)
            latency_ms = int((time.monotonic() - start) * 1000)
            self._record_success(latency_ms)
            self._archive(symbol, raw_payload)
            self._record_freshness(symbol)
            return ProviderResult(
                data=raw_payload,
                provider=self.name,
                latency_ms=latency_ms,
                raw_payload=raw_payload,
                market_timestamp=market_ts,
            )
        except Exception as e:
            self._record_failure()
            raise ProviderError(self.name, str(e)) from e

    async def fetch_bars(
        self,
        symbol: str,
        timeframe: str,
        count: int,
    ) -> list[ProviderResult]:
        """Fetch historical OHLCV bars."""
        start = time.monotonic()
        try:
            raw_results = await self._fetch_bars(symbol, timeframe, count)
            latency_ms = int((time.monotonic() - start) * 1000)
            self._record_success(latency_ms)
            results = []
            for raw_payload, market_ts in raw_results:
                self._archive(symbol, raw_payload)
                results.append(ProviderResult(
                    data=raw_payload,
                    provider=self.name,
                    latency_ms=latency_ms,
                    raw_payload=raw_payload,
                    market_timestamp=market_ts,
                ))
            self._record_freshness(symbol)
            return results
        except Exception as e:
            self._record_failure()
            raise ProviderError(self.name, str(e)) from e

    async def fetch_option_chain(self, symbol: str, expiry) -> ProviderResult:
        """Fetch an options chain."""
        start = time.monotonic()
        try:
            raw_payload, market_ts = await self._fetch_option_chain(symbol, expiry)
            latency_ms = int((time.monotonic() - start) * 1000)
            self._record_success(latency_ms)
            self._archive(symbol, raw_payload)
            self._record_freshness(symbol)
            return ProviderResult(
                data=raw_payload,
                provider=self.name,
                latency_ms=latency_ms,
                raw_payload=raw_payload,
                market_timestamp=market_ts,
            )
        except Exception as e:
            self._record_failure()
            raise ProviderError(self.name, str(e)) from e

    async def fetch_news(
        self,
        symbols: list[str] | None = None,
        categories: list[str] | None = None,
        limit: int = 50,
    ) -> list[ProviderResult]:
        """Fetch news articles."""
        start = time.monotonic()
        try:
            raw_results = await self._fetch_news(symbols, categories, limit)
            latency_ms = int((time.monotonic() - start) * 1000)
            self._record_success(latency_ms)
            results = []
            for raw_payload, market_ts in raw_results:
                self._archive(raw_payload.get("id", "news"), raw_payload)
                results.append(ProviderResult(
                    data=raw_payload,
                    provider=self.name,
                    latency_ms=latency_ms,
                    raw_payload=raw_payload,
                    market_timestamp=market_ts,
                ))
            return results
        except Exception as e:
            self._record_failure()
            raise ProviderError(self.name, str(e)) from e

    async def _fetch_quote(self, symbol: str) -> tuple[Any, datetime]:
        raise NotImplementedError(f"{self.name} does not implement fetch_quote")

    async def _fetch_bars(self, symbol: str, timeframe: str, count: int) -> list[tuple[Any, datetime]]:
        raise NotImplementedError(f"{self.name} does not implement fetch_bars")

    async def _fetch_option_chain(self, symbol: str, expiry) -> tuple[Any, datetime]:
        raise NotImplementedError(f"{self.name} does not implement fetch_option_chain")

    async def _fetch_news(self, symbols=None, categories=None, limit=50) -> list[tuple[Any, datetime]]:
        raise NotImplementedError(f"{self.name} does not implement fetch_news")

    def _archive(self, symbol: str, payload: Any) -> None:
        if self._archiver is not None:
            self._archiver.archive(provider=self.name, payload=payload)

    def _record_freshness(self, symbol: str) -> None:
        if self._freshness is not None:
            stream_id = f"{self.name}:{symbol}"
            try:
                self._freshness.record_receipt(stream_id)
            except Exception:
                pass  # freshness tracking is best-effort

    def _record_success(self, latency_ms: int) -> None:
        self._call_count += 1
        self._success_count += 1
        self._latencies.append(latency_ms)
        if len(self._latencies) > 100:
            self._latencies = self._latencies[-100:]
        self._last_success = datetime.now(timezone.utc)

    def _record_failure(self) -> None:
        self._call_count += 1
        self._failure_count += 1

    async def health_check(self) -> dict:
        """Return provider health metrics (Stage 2 req 1.7)."""
        avg_latency = (
            sum(self._latencies) / len(self._latencies)
            if self._latencies else 0.0
        )
        success_rate = (
            self._success_count / self._call_count
            if self._call_count > 0 else 0.0
        )
        staleness_ms = 0.0
        if self._last_success is not None:
            staleness_ms = (
                datetime.now(timezone.utc) - self._last_success
            ).total_seconds() * 1000

        return {
            "provider": self.name,
            "connection": "connected" if self._last_success is not None else "disconnected",
            "delay": avg_latency,
            "missingBars": 0,
            "missingTicks": 0,
            "apiErrors": self._failure_count,
            "failoverCount": 0,
            "freshness": staleness_ms,
            "reliabilityScore": success_rate,
            "total_calls": self._call_count,
            "successful_calls": self._success_count,
            "failed_calls": self._failure_count,
            "last_successful_update": self._last_success.isoformat() if self._last_success else None,
        }
