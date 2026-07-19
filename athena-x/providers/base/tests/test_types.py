"""Tests for provider base types."""
import pytest
from datetime import datetime, timezone, date
from athena_x_provider_base import Quote, Bar, Trade, OptionChain, OptionRow, NewsArticle


def test_quote_serialization():
    q = Quote(
        symbol="NVDA",
        last=128.45,
        bid=128.44,
        ask=128.46,
        timestamp=datetime.now(timezone.utc),
    )
    assert q.symbol == "NVDA"
    assert q.last == 128.45


def test_bar_serialization():
    b = Bar(timestamp=1700000000000, open=100, high=105, low=99, close=104, volume=1000)
    assert b.open == 100
    assert b.volume == 1000


def test_option_chain():
    chain = OptionChain(
        symbol="NVDA",
        expiry=date(2026, 7, 18),
        rows=[
            OptionRow(strike=125, expiry=date(2026, 7, 18), option_type="call", iv=0.45),
            OptionRow(strike=130, expiry=date(2026, 7, 18), option_type="put", iv=0.42),
        ],
    )
    assert chain.symbol == "NVDA"
    assert len(chain.rows) == 2


def test_news_article():
    a = NewsArticle(
        id="abc-123",
        source="reuters",
        headline="NVDA beats Q3 estimates",
        published_at=datetime.now(timezone.utc),
        symbols=["NVDA"],
        categories=["earnings"],
    )
    assert a.sentiment is None  # left blank in Stage 2
    assert a.source == "reuters"
