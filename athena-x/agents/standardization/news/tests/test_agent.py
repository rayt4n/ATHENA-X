"""Tests for News Standardization Agent."""
import pytest
from datetime import datetime, timezone
from athena_x_standardizer_news import NewsStandardizationAgent
from athena_x_standardizer_base import StandardizationContext
from athena_x_runtime_canonical_types import NewsRecord


@pytest.fixture
def agent():
    return NewsStandardizationAgent()


@pytest.fixture
def context():
    return StandardizationContext(
        provider="reuters", provider_version="1.0.0",
        raw_payload_id="raw-news-1", validation_id="val-news-1",
        validation_status="verified", confidence_score=0.9, quality_grade="A",
    )


def test_standardize_returns_news_record(agent, context):
    article = {
        "id": "abc-123",
        "source": "reuters",
        "headline": "NVDA beats Q3 estimates",
        "published_at": datetime.now(timezone.utc).isoformat(),
        "symbols": ["NVDA"],
        "categories": ["earnings"],
    }
    result = agent.standardize(article, context)
    assert isinstance(result, NewsRecord)
    assert result.source == "Reuters"  # normalized
    assert result.headline == "NVDA beats Q3 estimates"
    assert result.sentiment is None  # Stage 4 rule


def test_source_normalization(agent, context):
    """Various source spellings normalize to canonical form."""
    for raw, expected in [("reuters", "Reuters"), ("cnbc", "CNBC"), ("wsj", "Wall Street Journal")]:
        article = {
            "id": "x", "source": raw,
            "headline": "test", "published_at": datetime.now(timezone.utc).isoformat(),
        }
        result = agent.standardize(article, context)
        assert result.source == expected


def test_sentiment_always_none(agent, context):
    """Stage 4 rule: sentiment is always null."""
    article = {
        "id": "x", "source": "reuters",
        "headline": "test", "published_at": datetime.now(timezone.utc).isoformat(),
        "sentiment": 0.5,  # even if provided, we override to None in Stage 4
    }
    result = agent.standardize(article, context)
    assert result.sentiment is None


def test_category_normalization(agent, context):
    article = {
        "id": "x", "source": "cnbc",
        "headline": "test", "published_at": datetime.now(timezone.utc).isoformat(),
        "categories": ["M&A", "EARNINGS"],
    }
    result = agent.standardize(article, context)
    assert "mna" in result.categories
    assert "earnings" in result.categories


def test_language_defaults_to_english(agent, context):
    article = {
        "id": "x", "source": "reuters",
        "headline": "test", "published_at": datetime.now(timezone.utc).isoformat(),
    }
    result = agent.standardize(article, context)
    assert result.language == "en"
