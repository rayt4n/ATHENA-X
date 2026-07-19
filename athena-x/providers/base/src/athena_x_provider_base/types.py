"""Canonical data types produced by providers.

These are the OUTPUT types — what providers return after parsing their
provider-specific responses. Layer 3 (Standardization) further normalizes
these into the database canonical schema.
"""
from __future__ import annotations
from datetime import date, datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class Quote(BaseModel):
    """A real-time quote for a symbol."""
    model_config = ConfigDict(populate_by_name=True)
    symbol: str
    last: float
    bid: float | None = None
    ask: float | None = None
    high: float | None = None
    low: float | None = None
    open: float | None = None
    prev_close: float | None = None
    volume: int | None = None
    change: float | None = None
    change_percent: float | None = None
    timestamp: datetime


class Bar(BaseModel):
    """An OHLCV bar."""
    timestamp: int = Field(description="unix-millis")
    open: float
    high: float
    low: float
    close: float
    volume: int


class Trade(BaseModel):
    """An individual trade print."""
    symbol: str
    price: float
    size: int
    side: str | None = None  # 'buy' | 'sell' | 'unknown'
    timestamp: datetime


class OptionRow(BaseModel):
    """A single row in an options chain."""
    strike: float
    expiry: date
    option_type: str  # 'call' | 'put'
    bid: float | None = None
    ask: float | None = None
    last: float | None = None
    volume: int | None = None
    open_interest: int | None = None
    iv: float | None = None
    delta: float | None = None
    gamma: float | None = None
    theta: float | None = None
    vega: float | None = None
    rho: float | None = None


class OptionChain(BaseModel):
    """An options chain for a symbol on a specific expiry."""
    symbol: str
    expiry: date
    rows: list[OptionRow]


class NewsArticle(BaseModel):
    """A news article."""
    model_config = ConfigDict(populate_by_name=True)
    id: str
    source: str
    headline: str
    summary: str | None = None
    url: str | None = None
    raw_content: str | None = None
    published_at: datetime
    symbols: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    sentiment: float | None = None  # left blank in Stage 2; filled in Stage 10
