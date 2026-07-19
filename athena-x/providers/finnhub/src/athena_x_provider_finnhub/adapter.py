"""Finnhub provider adapter.

Uses Finnhub's REST API for quotes, company news, and earnings calendar.
WebSocket support for real-time trades is available but optional.

Requires FINNHUB_API_KEY environment variable.
"""
from __future__ import annotations
import os
from datetime import datetime, timezone
from typing import Any

import httpx

from athena_x_provider_base.base_adapter import BaseProviderAdapter
from athena_x_provider_base.provider import ProviderError


FINNHUB_BASE_URL = "https://finnhub.io/api/v1"


class FinnhubAdapter(BaseProviderAdapter):
    """Finnhub provider adapter.

    Layer 1 — Provider Adapters.
    """

    name = "finnhub"
    transport = "REST"
    asset_classes = ["equity", "etf", "currency"]

    def __init__(self, api_key: str | None = None, **kwargs):
        super().__init__(api_key=api_key, **kwargs)
        self._client: httpx.AsyncClient | None = None

    @property
    def _api_key(self) -> str:
        if not self.api_key:
            raise ProviderError("finnhub", "FINNHUB_API_KEY not set")
        return self.api_key

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers={"X-Finnhub-Token": self._api_key},
                timeout=httpx.Timeout(10.0, connect=5.0),
            )
        return self._client

    async def _fetch_quote(self, symbol: str) -> tuple[dict, datetime]:
        """Fetch a quote from Finnhub's /quote endpoint."""
        client = await self._get_client()
        url = f"{FINNHUB_BASE_URL}/quote"
        params = {"symbol": symbol, "token": self._api_key}

        resp = await client.get(url, params=params)
        if resp.status_code != 200:
            raise ProviderError("finnhub", f"HTTP {resp.status_code}: {resp.text[:200]}",
                                status_code=resp.status_code)

        data = resp.json()
        # Finnhub returns: {c: current, d: change, dp: change_percent,
        #                   h: high, l: low, o: open, pc: prev_close, t: timestamp}
        market_ts = datetime.now(timezone.utc)
        if data.get("t"):
            market_ts = datetime.fromtimestamp(data["t"], tz=timezone.utc)

        quote = {
            "symbol": symbol,
            "last": data.get("c", 0.0),
            "high": data.get("h"),
            "low": data.get("l"),
            "open": data.get("o"),
            "prev_close": data.get("pc"),
            "change": data.get("d"),
            "change_percent": data.get("dp"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "market_timestamp": market_ts.isoformat(),
        }
        return quote, market_ts

    async def _fetch_news(self, symbols=None, categories=None, limit=50) -> list[tuple[dict, datetime]]:
        """Fetch company news from Finnhub."""
        client = await self._get_client()
        from datetime import date, timedelta

        today = date.today()
        week_ago = today - timedelta(days=7)

        if symbols:
            # Company-specific news
            symbol = symbols[0]
            url = f"{FINNHUB_BASE_URL}/company-news"
            params = {
                "symbol": symbol,
                "from": week_ago.isoformat(),
                "to": today.isoformat(),
                "token": self._api_key,
            }
        else:
            # Market news
            url = f"{FINNHUB_BASE_URL}/news"
            params = {"category": "general", "token": self._api_key}

        resp = await client.get(url, params=params)
        if resp.status_code != 200:
            raise ProviderError("finnhub", f"HTTP {resp.status_code}", status_code=resp.status_code)

        data = resp.json()
        articles = []
        for item in data[:limit]:
            pub_ts = datetime.fromtimestamp(item.get("datetime", 0), tz=timezone.utc)
            article = {
                "id": str(item.get("id", "")),
                "source": "finnhub",
                "headline": item.get("headline", ""),
                "summary": item.get("summary", ""),
                "url": item.get("url", ""),
                "published_at": pub_ts.isoformat(),
                "symbols": [item.get("related", "")] if item.get("related") else [],
                "categories": ["news"],
                "sentiment": None,
            }
            articles.append((article, pub_ts))
        return articles

    async def fetch_company_news(self, symbol: str, days_back: int = 7) -> list[tuple[dict, datetime]]:
        """Convenience method for fetching company-specific news."""
        return await self._fetch_news(symbols=[symbol])

    async def close(self) -> None:
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
