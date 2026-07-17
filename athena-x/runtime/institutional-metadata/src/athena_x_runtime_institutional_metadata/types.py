"""
Institutional metadata — 10 mandatory fields per data record (Stage 2 req 1.5).

Every record that enters ATHENA-X (quote, trade, bar, news headline, option chain,
macro indicator) MUST carry this metadata. It travels with the payload through
the bus, gets archived alongside raw data, and is queryable in databases.

This is IN ADDITION TO the 10 bus event metadata fields from Stage 1.
"""
from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, field_validator


class DataStatus(str, Enum):
    """Freshness status of a data record."""
    FRESH = "fresh"
    DELAYED = "delayed"
    STALE = "stale"
    FAILED = "failed"


class AssetClass(str, Enum):
    EQUITY = "equity"
    ETF = "etf"
    INDEX = "index"
    FUTURE = "future"
    OPTION = "option"
    CURRENCY = "currency"
    COMMODITY = "commodity"
    YIELD = "yield"
    VOLATILITY = "volatility"
    CRYPTO = "crypto"
    NEWS = "news"
    MACRO = "macro"


class TradingSession(str, Enum):
    OVERNIGHT = "overnight"
    PRE_MARKET = "pre-market"
    REGULAR = "regular"
    POST_MARKET = "post-market"
    WEEKEND = "weekend"
    HOLIDAY = "holiday"


# Default confidence scores per provider (Stage 2 req 1.5: "initially provider default")
PROVIDER_DEFAULTS = {
    "databento":       0.98,  # institutional-grade, PIT-validated
    "polygon":         0.95,
    "finnhub":         0.93,
    "flashalpha":      0.92,
    "fred":            0.97,  # official US government data
    "alphavantage":    0.88,
    "trading-economics": 0.94,
    "yahoo":           0.85,
    "reuters":         0.95,
    "wsj":             0.93,
    "cnbc":            0.90,
    "cnn":             0.88,
    "sec":             0.99,  # regulatory filings, authoritative
    "polymarket":      0.85,
    "simulated":       0.50,  # dev only — never in production
}


class ProviderDefaults:
    """Lookup for default confidence scores per provider."""
    DEFAULTS = PROVIDER_DEFAULTS

    @classmethod
    def get_confidence(cls, provider: str) -> float:
        return cls.DEFAULTS.get(provider, 0.80)


class InstitutionalMetadata(BaseModel):
    """
    The 10 mandatory institutional metadata fields (Stage 2 req 1.5).

    Every data record carries this. Bus events wrap it alongside the Stage 1
    BusEventMeta (eventId, eventType, timestamp, etc.).
    """

    model_config = ConfigDict(populate_by_name=True, use_enum_values=True)

    # 1. Provider slug
    provider: str = Field(min_length=1, description="Source provider slug")

    # 2. Provider latency (ms)
    provider_latency: int = Field(ge=0, description="ms from request to response",
                                   alias="providerLatency")

    # 3. Download timestamp (when ATHENA-X received it)
    download_timestamp: datetime = Field(description="When ATHENA-X received it",
                                          alias="downloadTimestamp")

    # 4. Market timestamp (when the market event occurred)
    market_timestamp: datetime = Field(description="When the market event occurred",
                                        alias="marketTimestamp")

    # 5. Original timezone
    timezone: str = Field(default="UTC", description="Original timezone")

    # 6. Normalized symbol
    symbol: str = Field(min_length=1, description="Normalized symbol (e.g., 'BRK.B')")

    # 7. Asset class
    asset_class: AssetClass = Field(alias="assetClass")

    # 8. Confidence score (provider default initially)
    confidence_score: float = Field(ge=0.0, le=1.0, alias="confidenceScore",
                                     description="Initially provider default")

    # 9. Status (fresh/delayed/stale/failed)
    status: DataStatus = Field(default=DataStatus.FRESH)

    # 10. Trading session
    session: TradingSession = Field(default=TradingSession.REGULAR)

    @field_validator("download_timestamp", "market_timestamp")
    @classmethod
    def must_be_utc(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("timestamps must be timezone-aware (UTC)")
        return v.astimezone(timezone.utc)

    @field_validator("confidence_score")
    @classmethod
    def in_valid_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("confidence_score must be 0..1")
        return v
