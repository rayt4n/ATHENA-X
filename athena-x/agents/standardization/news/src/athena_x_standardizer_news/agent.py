"""News Standardization Agent (Stage 4 req 2.3).

Normalize: Sources, Categories, Symbols, Languages, URLs, Publication timestamps.

Rule: No sentiment (filled in Stage 10).

This agent is the ONLY writer to the news_db canonical database.
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any

from athena_x_standardizer_base import (
    StandardizationPipeline, StandardizationContext,
)
from athena_x_runtime_canonical_types import NewsRecord
from athena_x_runtime_schema_registry import SchemaRegistry, NEWS_RECORD_SCHEMA


# Source normalization (e.g., "Reuters", "reuters.com", "RTRS" → "Reuters")
SOURCE_NORMALIZATION = {
    "reuters": "Reuters",
    "reuters.com": "Reuters",
    "rtrs": "Reuters",
    "cnbc": "CNBC",
    "wsj": "Wall Street Journal",
    "wall street journal": "Wall Street Journal",
    "cnn": "CNN Business",
    "cnn business": "CNN Business",
    "sec": "SEC EDGAR",
    "federal-reserve": "Federal Reserve",
    "fed": "Federal Reserve",
    "treasury": "US Treasury",
}

# Category normalization
CATEGORY_NORMALIZATION = {
    "wire": "wire",
    "media": "media",
    "regulatory": "regulatory",
    "government": "government",
    "calendar": "calendar",
    "company": "company",
    "thematic": "thematic",
    "earnings": "earnings",
    "analyst": "analyst",
    "macro": "macro",
    "mna": "mna",
    "m&a": "mna",
    "geopolitical": "geopolitical",
    "energy": "energy",
    "semiconductor": "semiconductor",
}


class NewsStandardizationAgent:
    """Standardizes news articles into canonical NewsRecord format.

    Stage 4 rule: This agent is the ONLY writer to news_db.
    Stage 4 rule: No sentiment (left null).
    """

    def __init__(self, schema_registry: SchemaRegistry | None = None):
        self._pipeline = StandardizationPipeline()
        self._schema_registry = schema_registry or SchemaRegistry()
        if self._schema_registry.get("NewsRecord") is None:
            self._schema_registry.register(NEWS_RECORD_SCHEMA)

    def standardize(self, article: dict, context: StandardizationContext) -> NewsRecord:
        """Transform a news article into canonical NewsRecord."""
        # Normalize source
        source = article.get("source", "").lower()
        article["source"] = SOURCE_NORMALIZATION.get(source, article.get("source", "Unknown"))

        # Normalize categories
        categories = article.get("categories", [])
        article["categories"] = [
            CATEGORY_NORMALIZATION.get(c.lower(), c) for c in categories
        ]

        # Ensure language is set
        if "language" not in article:
            article["language"] = "en"

        # Sentiment is left null (Stage 4 rule)
        article["sentiment"] = None

        # Run through pipeline (handles timestamp, provenance, versioning)
        result = self._pipeline.standardize(article, context)
        canonical = result.canonical_record

        return NewsRecord(**canonical)
