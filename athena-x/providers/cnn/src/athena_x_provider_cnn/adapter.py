"""CNN Business provider adapter.

Fetches:
- Fear & Greed Index from production.dataviz.cnn.com
- CNN Business news RSS feed

No API key required.
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
import xml.etree.ElementTree as ET

import httpx

from athena_x_provider_base.base_adapter import BaseProviderAdapter
from athena_x_provider_base.provider import ProviderError


FEAR_GREED_URL = "https://production.dataviz.cnn.com/forecast/indices/fear-greed-graph/now"
CNN_NEWS_RSS = "https://rss.cnn.com/rss/money_news_international.xml"


class CNNAdapter(BaseProviderAdapter):
    """CNN Business provider."""

    name = "cnn"
    transport = "REST"
    asset_classes = ["news"]

    def __init__(self, api_key: str | None = None, **kwargs):
        super().__init__(api_key=None, **kwargs)
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers={"User-Agent": "ATHENA-X/0.1"},
                timeout=httpx.Timeout(10.0, connect=5.0),
            )
        return self._client

    async def fetch_fear_greed(self) -> dict:
        """Fetch the current Fear & Greed Index value."""
        client = await self._get_client()
        resp = await client.get(FEAR_GREED_URL)
        if resp.status_code != 200:
            raise ProviderError("cnn", f"HTTP {resp.status_code}", status_code=resp.status_code)

        data = resp.json()
        # CNN returns {'data': [{'value': 45, 'rating': 'Fear', ...}]}
        fear_greed_data = data.get("data", [])
        if not fear_greed_data:
            raise ProviderError("cnn", "No Fear & Greed data in response")

        latest = fear_greed_data[0]
        return {
            "value": latest.get("value"),
            "classification": latest.get("rating"),
            "timestamp": latest.get("x") or latest.get("timestamp"),
            "source": "cnn",
        }

    async def _fetch_news(self, symbols=None, categories=None, limit=50) -> list[tuple[dict, datetime]]:
        """Fetch CNN Business news from RSS feed."""
        client = await self._get_client()
        resp = await client.get(CNN_NEWS_RSS)
        if resp.status_code != 200:
            raise ProviderError("cnn", f"HTTP {resp.status_code}", status_code=resp.status_code)

        articles = self._parse_rss(resp.text, source="cnn", limit=limit)
        return articles

    def _parse_rss(self, rss_text: str, source: str, limit: int = 50) -> list[tuple[dict, datetime]]:
        """Parse an RSS feed into articles."""
        articles = []
        try:
            root = ET.fromstring(rss_text)
            items = root.findall(".//item")
            for item in items[:limit]:
                title = item.findtext("title", "")
                link = item.findtext("link", "")
                description = item.findtext("description", "")
                pub_date = item.findtext("pubDate", "")

                # Parse pubDate (RFC 822 format: "Wed, 17 Jul 2026 13:45:00 GMT")
                published_at = datetime.now(timezone.utc)
                if pub_date:
                    try:
                        from email.utils import parsedate_to_datetime
                        published_at = parsedate_to_datetime(pub_date)
                        if published_at.tzinfo is None:
                            published_at = published_at.replace(tzinfo=timezone.utc)
                    except Exception:
                        pass

                article = {
                    "id": link or title,  # use URL as ID
                    "source": source,
                    "headline": title,
                    "summary": description,
                    "url": link,
                    "published_at": published_at.isoformat(),
                    "symbols": [],  # symbol extraction is Stage 3 (standardization)
                    "categories": ["news"],
                    "sentiment": None,  # left blank — Stage 10 fills this
                }
                articles.append((article, published_at))
        except ET.ParseError as e:
            raise ProviderError(source, f"RSS parse error: {e}")

        return articles

    async def close(self) -> None:
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
