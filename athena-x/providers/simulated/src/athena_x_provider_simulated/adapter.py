"""Simulated provider for development and testing.

Generates deterministic mock data using a seeded random generator.
NEVER used in production — the provider failover chain excludes it.
"""
from __future__ import annotations
import random
from datetime import datetime, timezone, timedelta
from typing import Any

from athena_x_provider_base import Quote, Bar
from athena_x_provider_base.base_adapter import BaseProviderAdapter
from athena_x_provider_base.provider import ProviderResult


# Base prices for common symbols (deterministic starting points)
BASE_PRICES = {
    "SPY": 450.0, "ES": 4500.0, "SPX": 4500.0,
    "QQQ": 380.0, "NQ": 16000.0,
    "DIA": 380.0, "IWM": 200.0, "SOXX": 200.0,
    "VIX": 15.0, "VVIX": 90.0, "MOVE": 80.0,
    "TNX": 4.5, "DXY": 100.0, "USDJPY": 150.0,
    "Gold": 2000.0, "Oil": 80.0, "Copper": 4.0,
    "BTC-USD": 65000.0, "ETH-USD": 3500.0,
    "NVDA": 128.0, "AAPL": 225.0, "MSFT": 420.0,
    "TSLA": 250.0, "META": 500.0, "AMZN": 185.0, "GOOGL": 175.0,
}


class SimulatedAdapter(BaseProviderAdapter):
    """Simulated provider. Generates deterministic mock quotes/bars."""

    name = "simulated"
    transport = "in-process"
    asset_classes = ["equity", "etf", "index", "future", "currency",
                     "commodity", "yield", "volatility", "crypto"]

    def __init__(self, seed: int = 42, **kwargs):
        super().__init__(api_key=None, **kwargs)
        self._rng = random.Random(seed)
        self._prices = dict(BASE_PRICES)

    async def _fetch_quote(self, symbol: str) -> tuple[dict, datetime]:
        """Generate a simulated quote with a small random walk."""
        base = self._prices.get(symbol, 100.0)
        # Random walk: ±0.5%
        change_pct = self._rng.gauss(0, 0.005)
        new_price = base * (1 + change_pct)
        self._prices[symbol] = new_price

        bid = new_price - self._rng.uniform(0.01, 0.05)
        ask = new_price + self._rng.uniform(0.01, 0.05)
        now = datetime.now(timezone.utc)

        quote = {
            "symbol": symbol,
            "last": round(new_price, 4),
            "bid": round(bid, 4),
            "ask": round(ask, 4),
            "high": round(new_price * 1.01, 4),
            "low": round(new_price * 0.99, 4),
            "open": round(base, 4),
            "prev_close": round(base, 4),
            "volume": self._rng.randint(100000, 5000000),
            "change": round(new_price - base, 4),
            "change_percent": round(change_pct * 100, 4),
            "timestamp": now.isoformat(),
        }
        return quote, now

    async def _fetch_bars(self, symbol: str, timeframe: str, count: int) -> list[tuple[dict, datetime]]:
        """Generate simulated historical bars."""
        base = self._prices.get(symbol, 100.0)
        bars = []
        now = datetime.now(timezone.utc)

        # Time delta per timeframe
        deltas = {
            "1m": timedelta(minutes=1), "5m": timedelta(minutes=5),
            "15m": timedelta(minutes=15), "30m": timedelta(minutes=30),
            "1h": timedelta(hours=1), "4h": timedelta(hours=4),
            "1D": timedelta(days=1), "1W": timedelta(weeks=1),
            "1M": timedelta(days=30),
        }
        delta = deltas.get(timeframe, timedelta(minutes=1))

        for i in range(count):
            ts = now - delta * (count - i)
            open_p = base * (1 + self._rng.gauss(0, 0.01))
            close_p = open_p * (1 + self._rng.gauss(0, 0.005))
            high_p = max(open_p, close_p) * (1 + self._rng.uniform(0, 0.005))
            low_p = min(open_p, close_p) * (1 - self._rng.uniform(0, 0.005))

            bar = {
                "symbol": symbol,
                "timestamp": int(ts.timestamp() * 1000),
                "open": round(open_p, 4),
                "high": round(high_p, 4),
                "low": round(low_p, 4),
                "close": round(close_p, 4),
                "volume": self._rng.randint(10000, 1000000),
            }
            bars.append((bar, ts))
            base = close_p  # next bar starts where this one ended

        return bars

    async def health_check(self) -> dict:
        health = await super().health_check()
        health["connection"] = "connected"
        health["reliabilityScore"] = 1.0
        return health
