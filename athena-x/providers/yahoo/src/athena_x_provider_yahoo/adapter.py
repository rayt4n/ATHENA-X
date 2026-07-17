"""Yahoo Finance provider adapter.

Uses Yahoo's public (undocumented) API endpoints:
  - /v8/finance/chart/{symbol} — historical bars + quotes
  - /v7/finance/quote?symbols=... — batch quotes (currently rate-limited)

No API key required, but rate-limited. Falls back to /v8/finance/chart
for individual quotes which is more reliable.
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any

import httpx

from athena_x_provider_base.base_adapter import BaseProviderAdapter
from athena_x_provider_base.provider import ProviderError


YAHOO_BASE_URL = "https://query1.finance.yahoo.com"
YAHOO_CHART_URL = f"{YAHOO_BASE_URL}/v8/finance/chart/{{symbol}}"


class YahooAdapter(BaseProviderAdapter):
    """Yahoo Finance provider adapter.

    Layer 1 — Provider Adapters.
    ONLY downloads data. NEVER calculates, validates, or standardizes.
    """

    name = "yahoo"
    transport = "REST"
    asset_classes = ["equity", "etf", "index", "currency", "commodity",
                     "yield", "volatility", "future"]

    def __init__(self, api_key: str | None = None, **kwargs):
        # Yahoo doesn't require an API key for public endpoints
        super().__init__(api_key=None, **kwargs)
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers={
                    "User-Agent": "Mozilla/5.0 (ATHENA-X research)",
                    "Accept": "application/json",
                },
                timeout=httpx.Timeout(10.0, connect=5.0),
            )
        return self._client

    async def _fetch_quote(self, symbol: str) -> tuple[dict, datetime]:
        """Fetch a quote using Yahoo's chart endpoint."""
        client = await self._get_client()
        url = YAHOO_CHART_URL.format(symbol=symbol)
        params = {"interval": "1m", "range": "1d"}

        resp = await client.get(url, params=params)
        if resp.status_code != 200:
            raise ProviderError(
                "yahoo",
                f"HTTP {resp.status_code}: {resp.text[:200]}",
                status_code=resp.status_code,
            )

        data = resp.json()
        result = data.get("chart", {}).get("result", [])
        if not result:
            raise ProviderError("yahoo", f"No data for symbol: {symbol}")

        chart = result[0]
        meta = chart.get("meta", {})

        # Extract quote fields from metadata
        quote = {
            "symbol": meta.get("symbol", symbol),
            "last": meta.get("regularMarketPrice", 0.0),
            "bid": meta.get("bid", 0.0) or None,
            "ask": meta.get("ask", 0.0) or None,
            "high": meta.get("regularMarketDayHigh", 0.0) or None,
            "low": meta.get("regularMarketDayLow", 0.0) or None,
            "open": meta.get("regularMarketOpen", 0.0) or None,
            "prev_close": meta.get("chartPreviousClose", meta.get("previousClose", 0.0)) or None,
            "volume": meta.get("regularMarketVolume", 0) or None,
            "change": meta.get("regularMarketChange", None),
            "change_percent": meta.get("regularMarketChangePercent", None),
            "currency": meta.get("currency", "USD"),
            "exchange": meta.get("exchangeName", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Use the most recent bar timestamp as market_timestamp if available
        timestamps = chart.get("timestamp", [])
        market_ts = datetime.now(timezone.utc)
        if timestamps:
            from datetime import datetime as dt
            market_ts = dt.fromtimestamp(timestamps[-1], tz=timezone.utc)

        return quote, market_ts

    async def _fetch_bars(self, symbol: str, timeframe: str, count: int) -> list[tuple[dict, datetime]]:
        """Fetch historical bars from Yahoo."""
        client = await self._get_client()
        url = YAHOO_CHART_URL.format(symbol=symbol)

        # Map our timeframes to Yahoo intervals
        interval_map = {
            "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
            "1h": "60m", "4h": "60m",  # Yahoo doesn't have 4h, use 60m
            "1D": "1d", "1W": "1wk", "1M": "1mo",
        }
        yahoo_interval = interval_map.get(timeframe, "1m")

        # Range: estimate based on count × interval
        range_map = {
            "1m": "1d", "5m": "5d", "15m": "5d", "30m": "1mo",
            "1h": "1mo", "1D": "1y", "1W": "5y", "1M": "10y",
        }
        yahoo_range = range_map.get(timeframe, "1mo")

        params = {"interval": yahoo_interval, "range": yahoo_range}

        resp = await client.get(url, params=params)
        if resp.status_code != 200:
            raise ProviderError("yahoo", f"HTTP {resp.status_code}", status_code=resp.status_code)

        data = resp.json()
        result = data.get("chart", {}).get("result", [])
        if not result:
            raise ProviderError("yahoo", f"No data for {symbol}")

        chart = result[0]
        timestamps = chart.get("timestamp", [])
        indicators = chart.get("indicators", {})
        quote_data = indicators.get("quote", [{}])[0]

        opens = quote_data.get("open", [])
        highs = quote_data.get("high", [])
        lows = quote_data.get("low", [])
        closes = quote_data.get("close", [])
        volumes = indicators.get("adjclose", [{}])[0].get("adjclose", closes) if "adjclose" in indicators else closes
        vol_data = indicators.get("quote", [{}])[0].get("volume", [])

        bars = []
        for i, ts in enumerate(timestamps):
            if i >= len(closes) or closes[i] is None:
                continue
            bar = {
                "symbol": symbol,
                "timestamp": ts * 1000,  # to millis
                "open": opens[i] if i < len(opens) else None,
                "high": highs[i] if i < len(highs) else None,
                "low": lows[i] if i < len(lows) else None,
                "close": closes[i],
                "volume": vol_data[i] if i < len(vol_data) else 0,
            }
            from datetime import datetime as dt
            bars.append((bar, dt.fromtimestamp(ts, tz=timezone.utc)))
            if len(bars) >= count:
                break

        return bars

    async def close(self) -> None:
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
