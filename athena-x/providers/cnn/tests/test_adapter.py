"""Tests for CNN provider."""
import pytest
import httpx
from athena_x_provider_cnn import CNNAdapter


def mock_fear_greed_response() -> dict:
    return {
        "data": [{
            "value": 45,
            "rating": "Fear",
            "x": 1700000000,
        }]
    }


def mock_cnn_rss() -> str:
    return """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
    <channel>
        <title>CNNMoney</title>
        <item>
            <title>NVDA beats Q3 estimates</title>
            <link>https://example.com/article1</link>
            <description>Nvidia reported strong earnings.</description>
            <pubDate>Wed, 17 Jul 2026 13:45:00 GMT</pubDate>
        </item>
        <item>
            <title>Fed signals rate cut</title>
            <link>https://example.com/article2</link>
            <description>The Federal Reserve indicated a possible rate cut.</description>
            <pubDate>Wed, 17 Jul 2026 14:00:00 GMT</pubDate>
        </item>
    </channel>
</rss>"""


@pytest.fixture
async def provider():
    def handler(request):
        url = str(request.url)
        if "fear-greed" in url:
            return httpx.Response(200, json=mock_fear_greed_response())
        elif "rss" in url:
            return httpx.Response(200, text=mock_cnn_rss())
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    p = CNNAdapter()
    p._client = httpx.AsyncClient(transport=transport)
    yield p
    await p.close()


async def test_fetch_fear_greed(provider):
    result = await provider.fetch_fear_greed()
    assert result["value"] == 45
    assert result["classification"] == "Fear"
    assert result["source"] == "cnn"


async def test_fetch_news_parses_rss(provider):
    articles = await provider._fetch_news(limit=10)
    assert len(articles) == 2
    article, ts = articles[0]
    assert article["headline"] == "NVDA beats Q3 estimates"
    assert article["url"] == "https://example.com/article1"
    assert article["source"] == "cnn"
    assert article["sentiment"] is None  # left blank in Stage 2


async def test_news_articles_have_timestamps(provider):
    articles = await provider._fetch_news(limit=10)
    for article, ts in articles:
        assert ts is not None
        assert ts.year == 2026
