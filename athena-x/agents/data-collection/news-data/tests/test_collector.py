"""Tests for NewsDataCollector."""
import pytest
from datetime import datetime, timezone
from athena_x_runtime_event_bus import InMemoryBusClient
from athena_x_collector_base import CollectorConfig
from athena_x_collector_news_data import NewsDataCollector, NEWS_SOURCES


@pytest.fixture
async def setup():
    bus = InMemoryBusClient()
    config = CollectorConfig(
        collector_id="news:reuters",
        symbol="reuters",
        asset_class="news",
        poll_interval_seconds=30.0,
        expected_frequency_seconds=30.0,
    )
    collector = NewsDataCollector(
        config=config, bus=bus, source="reuters", category="wire",
    )
    yield bus, collector
    await collector.stop()
    await bus.close()


def test_14_news_sources_defined():
    """14 news sources are defined (excluding Bloomberg unless licensed)."""
    assert len(NEWS_SOURCES) >= 13
    sources = [s for s, _, _ in NEWS_SOURCES]
    assert "reuters" in sources
    assert "cnbc" in sources
    assert "wsj" in sources
    assert "cnn" in sources
    assert "sec" in sources
    assert "federal-reserve" in sources
    assert "economic-calendar" in sources


def test_news_sources_split_by_category():
    """Sources are split by category (wire/media/regulatory/etc.)."""
    categories = {c for _, c, _ in NEWS_SOURCES}
    assert "wire" in categories
    assert "media" in categories
    assert "regulatory" in categories
    assert "government" in categories
    assert "calendar" in categories
    assert "company" in categories
    assert "thematic" in categories


async def test_fetch_returns_articles_with_10_fields(setup):
    """Each article has the 10 mandatory fields."""
    bus, collector = setup
    articles, ts = await collector.fetch_data()

    assert len(articles) >= 1
    for a in articles:
        # 10 mandatory fields (Stage 2 req 1.3)
        assert "source" in a
        assert "published_at" in a  # timestamp
        assert "symbols" in a
        assert "categories" in a
        assert "headline" in a
        assert "summary" in a
        assert "url" in a
        assert "raw_content" in a
        assert "sentiment" in a
        assert "provider" in a


async def test_sentiment_is_blank(setup):
    """Stage 2 rule: sentiment is left blank (None)."""
    bus, collector = setup
    articles, ts = await collector.fetch_data()
    for a in articles:
        assert a["sentiment"] is None


async def test_articles_include_source(setup):
    """Each article includes its source."""
    bus, collector = setup
    articles, ts = await collector.fetch_data()
    for a in articles:
        assert a["source"] == "reuters"
        assert a["provider"] == "reuters"


async def test_collector_publishes_news_event(setup):
    """Collector publishes news:headline-received events."""
    bus, collector = setup

    received = []
    async def handler(event):
        received.append(event)
    await bus.subscribe("news:headline-received", handler)

    await collector.collect_once()

    assert len(received) >= 1
    event = received[0]
    assert event.payload["metadata"]["symbol"] == "reuters"
    assert event.payload["metadata"]["assetClass"] == "news"


async def test_company_news_includes_mag7_symbols():
    """MAG7 company news includes relevant symbols."""
    bus = InMemoryBusClient()
    config = CollectorConfig(
        collector_id="news:company-news-mag7",
        symbol="company-news-mag7",
        asset_class="news",
    )
    collector = NewsDataCollector(
        config=config, bus=bus, source="company-news-mag7", category="company",
    )
    articles, ts = await collector.fetch_data()
    for a in articles:
        # Company news should include a MAG7 symbol
        assert len(a["symbols"]) >= 1
        mag7 = ["NVDA", "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA"]
        assert any(s in mag7 for s in a["symbols"])
    await collector.stop()
    await bus.close()
