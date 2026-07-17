"""Bar cache - Stage 7 req 10.

Repository -> Bar Cache -> Indicators

EMA, MACD, Bollinger, ATR all use identical OHLCV bars.
Instead of querying repeatedly, a shared bar cache eliminates redundant reads.
"""
from __future__ import annotations
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from threading import RLock
from typing import Any


@dataclass
class CachedBars:
    """Cached OHLCV bars for a symbol+timeframe."""
    symbol: str
    timeframe: str
    bars: list[dict]
    fetched_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def age_seconds(self) -> float:
        return (datetime.now(timezone.utc) - self.fetched_at).total_seconds()

    @property
    def is_stale(self) -> bool:
        """Bars older than 60 seconds are considered stale."""
        return self.age_seconds > 60.0

    @property
    def closes(self) -> list[float]:
        return [b.get("close", 0) for b in self.bars]

    @property
    def opens(self) -> list[float]:
        return [b.get("open", 0) for b in self.bars]

    @property
    def highs(self) -> list[float]:
        return [b.get("high", 0) for b in self.bars]

    @property
    def lows(self) -> list[float]:
        return [b.get("low", 0) for b in self.bars]

    @property
    def volumes(self) -> list[int]:
        return [b.get("volume", 0) for b in self.bars]


class BarCache:
    """Shared bar cache for all TA agents.

    Eliminates redundant repository reads when multiple indicators
    need the same OHLCV data.

    Usage:
        cache = BarCache()
        bars = await cache.get_bars(repo, "SPY", "15m", count=100)
        # Multiple indicators can now use `bars` without re-querying
    """

    def __init__(self, max_entries: int = 1000, ttl_seconds: float = 60.0):
        self._cache: OrderedDict[str, CachedBars] = OrderedDict()
        self._lock = RLock()
        self._max_entries = max_entries
        self._ttl = ttl_seconds
        self._hits = 0
        self._misses = 0

    async def get_bars(
        self,
        repo: Any,
        symbol: str,
        timeframe: str,
        count: int = 100,
    ) -> CachedBars:
        """Get bars from cache or fetch from repository."""
        key = f"{symbol}:{timeframe}:{count}"

        with self._lock:
            cached = self._cache.get(key)
            if cached and not cached.is_stale:
                self._hits += 1
                return cached
            self._misses += 1

        # Fetch from repository
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=count)  # rough estimate
        result = await repo.query_bars(symbol, timeframe, start, now)

        bars = result.records if result.records else []
        cached_bars = CachedBars(symbol=symbol, timeframe=timeframe, bars=bars)

        with self._lock:
            self._cache[key] = cached_bars
            # Evict oldest if over capacity
            while len(self._cache) > self._max_entries:
                self._cache.popitem(last=False)

        return cached_bars

    def invalidate(self, symbol: str | None = None) -> None:
        """Invalidate cache entries (optionally for a specific symbol)."""
        with self._lock:
            if symbol is None:
                self._cache.clear()
            else:
                keys_to_remove = [k for k in self._cache if k.startswith(f"{symbol}:")]
                for k in keys_to_remove:
                    del self._cache[k]

    def get_stats(self) -> dict:
        with self._lock:
            return {
                "cache_size": len(self._cache),
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": self._hits / (self._hits + self._misses) if (self._hits + self._misses) > 0 else 0.0,
            }
