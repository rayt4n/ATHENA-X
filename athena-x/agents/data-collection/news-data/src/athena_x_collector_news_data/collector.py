"""News collector — 14 sources split by category (Stage 2 req 1.3).

Sources:
  Wire services: Reuters, Bloomberg (if licensing permits)
  Financial media: CNBC, WSJ, CNN Business
  Regulatory: SEC Filings
  Government: Federal Reserve, Treasury
  Calendars: Economic Calendar, Earnings Calendar
  Company news: MAG7 (NVDA, AAPL, MSFT, GOOGL, AMZN, META, TSLA)
  Thematic: Geopolitical, Energy, Semiconductor

Each article includes 10 fields:
  source, timestamp, symbols, categories, headline, summary, url,
  raw_content (where permitted), sentiment (left blank — Stage 10), provider

No AI analysis at this stage.
"""
from __future__ import annotations
import random
from datetime import datetime, timezone, timedelta
from typing import Any

from athena_x_collector_base import BaseCollector, CollectorConfig


NEWS_SOURCES = [
    # Wire services
    ("reuters", "wire", "Reuters"),
    # ("bloomberg", "wire", "Bloomberg"),  # uncomment if licensing permits
    # Financial media
    ("cnbc", "media", "CNBC"),
    ("wsj", "media", "Wall Street Journal"),
    ("cnn", "media", "CNN Business"),
    # Regulatory
    ("sec", "regulatory", "SEC Filings"),
    # Government
    ("federal-reserve", "government", "Federal Reserve"),
    ("treasury", "government", "US Treasury"),
    # Calendars
    ("economic-calendar", "calendar", "Economic Calendar"),
    ("earnings-calendar", "calendar", "Earnings Calendar"),
    # Company news (MAG7)
    ("company-news-mag7", "company", "MAG7 Company News"),
    # Thematic
    ("geopolitical", "thematic", "Geopolitical News"),
    ("energy", "thematic", "Energy News"),
    ("semiconductor", "thematic", "Semiconductor News"),
]


MAG7_SYMBOLS = ["NVDA", "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA"]


class NewsDataCollector(BaseCollector):
    """News collector — fetches articles from a single source.

    Stage 2 rule: NO AI analysis. Sentiment is left blank (null).
    """

    def __init__(
        self,
        config: CollectorConfig,
        source: str,
        category: str,
        **kwargs,
    ):
        super().__init__(config=config, **kwargs)
        self._source = source
        self._category = category
        self._rng = random.Random(hash(source) & 0xFFFFFFFF)
        self._article_counter = 0

    async def fetch_data(self) -> tuple[list[dict], datetime]:
        """Fetch news articles (list)."""
        now = datetime.now(timezone.utc)
        articles = []

        for _ in range(self._rng.randint(1, 5)):
            self._article_counter += 1
            article = {
                "id": f"{self._source}-{self._article_counter}",
                "source": self._source,
                "headline": self._generate_headline(),
                "summary": self._generate_summary(),
                "url": f"https://example.com/{self._source}/{self._article_counter}",
                "raw_content": None,  # only set where permitted
                "published_at": (now - timedelta(minutes=self._rng.randint(0, 60))).isoformat(),
                "symbols": self._get_symbols(),
                "categories": [self._category],
                "sentiment": None,  # LEFT BLANK — Stage 10 fills this
                "provider": self._source,
            }
            articles.append(article)

        return articles, now

    def _generate_headline(self) -> str:
        templates = [
            f"{self._rng.choice(MAG7_SYMBOLS)} reports strong quarterly earnings",
            f"Fed signals potential rate change at next FOMC meeting",
            f"{self._rng.choice(['Oil', 'Gold', 'Copper'])} prices surge on supply concerns",
            f"Semiconductor sector outlook: analyst views mixed",
            f"Geopolitical tensions escalate in {self._rng.choice(['Middle East', 'Asia', 'Europe'])}",
            f"SEC files new disclosure for {self._rng.choice(MAG7_SYMBOLS)}",
            f"Earnings calendar: key reports this week",
            f"Economic data: CPI prints below expectations",
        ]
        return self._rng.choice(templates)

    def _generate_summary(self) -> str:
        return f"Summary of {self._source} article. Full content available at URL."

    def _get_symbols(self) -> list[str]:
        if self._category == "company":
            return [self._rng.choice(MAG7_SYMBOLS)]
        elif self._category == "thematic" and self._source == "semiconductor":
            return ["NVDA", "AMD", "INTC", "SOXX"]
        elif self._category == "thematic" and self._source == "energy":
            return ["XOM", "CVX", "OIL"]
        return []

    def _get_provider_name(self) -> str:
        return self._source

    def get_event_type(self) -> str:
        return "news:headline-received"
