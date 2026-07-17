"""Event Classifier - classifies raw news into structured NewsEvent objects."""
from __future__ import annotations
import re
from typing import Any
from athena_x_plugin_news_base import NewsEvent, NewsCategory, EventImportance
from athena_x_runtime_logger import get_logger

log = get_logger("narrative.classifier")


# Keyword-based classification rules (V1 — NLP in V2)
CLASSIFICATION_RULES = {
    NewsCategory.ECONOMIC: {
        "keywords": ["CPI", "PPI", "NFP", "GDP", "retail sales", "PMI", "ISM", "housing",
                      "consumer confidence", "unemployment", "inflation", "jobless claims"],
        "importance": EventImportance.HIGH,
    },
    NewsCategory.FED: {
        "keywords": ["FOMC", "Powell", "Fed Governor", "Beige Book", "Fed Minutes",
                      "Federal Reserve", "rate cut", "rate hike", "fed funds"],
        "importance": EventImportance.CRITICAL,
    },
    NewsCategory.TREASURY: {
        "keywords": ["auction", "debt issuance", "TGA", "Treasury statement", "bond auction"],
        "importance": EventImportance.MEDIUM,
    },
    NewsCategory.EARNINGS: {
        "keywords": ["EPS", "earnings", "Q1", "Q2", "Q3", "Q4", "revenue beat", "guidance",
                      "buyback", "dividend"],
        "importance": EventImportance.HIGH,
    },
    NewsCategory.GEOPOLITICAL: {
        "keywords": ["war", "sanctions", "trade", "Taiwan", "Middle East", "China",
                      "Europe", "NATO", "Russia", "Ukraine"],
        "importance": EventImportance.HIGH,
    },
    NewsCategory.ENERGY: {
        "keywords": ["OPEC", "oil", "LNG", "natural gas", "crude", "barrel", "production cut"],
        "importance": EventImportance.MEDIUM,
    },
    NewsCategory.SEMICONDUCTOR: {
        "keywords": ["NVIDIA", "NVDA", "AMD", "TSMC", "Broadcom", "AVGO", "Intel", "INTC",
                      "Qualcomm", "QCOM", "ARM", "Samsung", "chip", "semiconductor", "wafer"],
        "importance": EventImportance.HIGH,
    },
    NewsCategory.REGULATORY: {
        "keywords": ["SEC", "CFTC", "OCC", "DOJ", "antitrust", "probe", "investigation",
                      "fine", "penalty"],
        "importance": EventImportance.MEDIUM,
    },
    NewsCategory.ALTERNATIVE: {
        "keywords": ["Polymarket", "prediction market", "press release", "announcement"],
        "importance": EventImportance.LOW,
    },
}

# Symbol extraction patterns
SYMBOL_PATTERNS = [
    (re.compile(r"\b(NVDA|AAPL|MSFT|GOOGL|AMZN|META|TSLA)\b"), "mag7"),
    (re.compile(r"\b(ES|SPY|SPX|QQQ|NQ|IWM|DIA|SOXX|SMH)\b"), "index"),
    (re.compile(r"\b(VIX|VVIX|MOVE|TNX|DXY)\b"), "indicator"),
    (re.compile(r"\b(Gold|Oil|Copper|Silver)\b"), "commodity"),
    (re.compile(r"\b(XLK|XLF|XLV|XLY|XLI|XLE|XLP|XLB|XLU|XLRE|XLC)\b"), "sector"),
]

# Region detection
REGION_PATTERNS = {
    "US": re.compile(r"\b(US|United States|America|Wall Street|Fed|Treasury)\b", re.I),
    "EU": re.compile(r"\b(Europe|EU|Eurozone|ECB|DAX|FTSE|CAC)\b", re.I),
    "CN": re.compile(r"\b(China|Chinese|Beijing|Shanghai|PBoC)\b", re.I),
    "JP": re.compile(r"\b(Japan|Japanese|Tokyo|BoJ|Nikkei)\b", re.I),
    "UK": re.compile(r"\b(UK|Britain|British|BoE|FTSE)\b", re.I),
    "Global": re.compile(r"\b(global|worldwide|international)\b", re.I),
}


class EventClassifier:
    """Classifies raw news articles into structured NewsEvent objects.

    Stage 10: Every news item becomes a structured event with category,
    region, symbols, importance, and confidence.
    """

    def classify(self, raw_article: dict) -> NewsEvent:
        """Classify a raw news article."""
        from uuid import uuid4
        headline = raw_article.get("headline", "")
        source = raw_article.get("source", "Unknown")
        timestamp_str = raw_article.get("published_at") or raw_article.get("timestamp", "")

        # Parse timestamp
        from datetime import datetime, timezone
        try:
            if isinstance(timestamp_str, str):
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            else:
                timestamp = datetime.now(timezone.utc)
        except Exception:
            timestamp = datetime.now(timezone.utc)

        # Classify category
        category, importance = self._classify_category(headline)

        # Extract symbols
        symbols = self._extract_symbols(headline)

        # Detect region
        region = self._detect_region(headline)

        # Detect related assets
        related_assets = self._detect_related_assets(headline, category, symbols)

        return NewsEvent(
            event_id=str(uuid4()),
            timestamp=timestamp,
            source=source,
            headline=headline,
            category=category,
            importance=importance,
            symbols=symbols,
            region=region,
            related_assets=related_assets,
            confidence=0.85,
            summary=raw_article.get("summary", ""),
            url=raw_article.get("url", ""),
        )

    def _classify_category(self, headline: str) -> tuple[NewsCategory, EventImportance]:
        """Classify the category based on headline keywords."""
        headline_lower = headline.lower()
        for category, rules in CLASSIFICATION_RULES.items():
            for keyword in rules["keywords"]:
                if keyword.lower() in headline_lower:
                    return category, rules["importance"]
        return NewsCategory.BREAKING, EventImportance.MEDIUM

    def _extract_symbols(self, headline: str) -> list[str]:
        """Extract stock symbols from headline."""
        symbols = set()
        for pattern, _ in SYMBOL_PATTERNS:
            matches = pattern.findall(headline)
            symbols.update(matches)
        return list(symbols)

    def _detect_region(self, headline: str) -> str:
        """Detect the geographic region."""
        for region, pattern in REGION_PATTERNS.items():
            if pattern.search(headline):
                return region
        return "US"  # default

    def _detect_related_assets(self, headline: str, category: NewsCategory, symbols: list[str]) -> list[str]:
        """Detect related assets based on category + symbols."""
        related = set(symbols)
        # Add related assets based on category
        if category == NewsCategory.ECONOMIC:
            related.update(["ES", "SPY", "TNX", "DXY", "VIX"])
        elif category == NewsCategory.FED:
            related.update(["ES", "SPY", "TNX", "DXY", "Gold"])
        elif category == NewsCategory.SEMICONDUCTOR:
            related.update(["SOXX", "QQQ", "NVDA"])
        elif category == NewsCategory.ENERGY:
            related.update(["Oil", "XLE"])
        elif category == NewsCategory.GEOPOLITICAL:
            related.update(["VIX", "Gold", "Oil"])
        return list(related)
