"""Shared test fixtures for Layer 2 indicators."""
import pytest
from datetime import datetime, timezone, timedelta
from athena_x_runtime_repository_interface import QueryResult


class FakeMarketRepository:
    """Fake repository that returns deterministic OHLCV bars."""
    async def query_bars(self, symbol, timeframe, start, end):
        bars = []
        base_price = 450.0 if symbol == "SPY" else 100.0
        base = datetime.now(timezone.utc) - timedelta(days=200)
        for i in range(200):
            ts = base + timedelta(minutes=i * 15)
            price = base_price + i * 0.1 + (i % 7) * 0.5 - (i % 3) * 0.3
            bars.append({
                "symbol": symbol,
                "timeframe": timeframe,
                "timestamp": ts.isoformat(),
                "open": round(price - 0.2, 4),
                "high": round(price + 0.5, 4),
                "low": round(price - 0.5, 4),
                "close": round(price, 4),
                "volume": 100000 + i * 100,
            })
        return QueryResult(records=bars, count=len(bars))

    async def read_quote(self, symbol):
        return None

    async def write_quote(self, record):
        pass

    async def write_bar(self, record):
        pass

    async def supersede(self, record_id, corrected):
        pass

    async def get_history(self, symbol, limit=100):
        return QueryResult(records=[], count=0)


@pytest.fixture
def repo():
    return FakeMarketRepository()
