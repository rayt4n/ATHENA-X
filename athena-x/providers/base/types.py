"""Shared types for all providers."""
from __future__ import annotations
from datetime import date, datetime
from typing import Protocol
from pydantic import BaseModel


class Quote(BaseModel):
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
    timestamp: int  # unix-millis
    open: float
    high: float
    low: float
    close: float
    volume: int


class OptionRow(BaseModel):
    strike: float
    call_iv: float | None = None
    call_vol: int | None = None
    call_oi: int | None = None
    call_delta: float | None = None
    put_iv: float | None = None
    put_vol: int | None = None
    put_oi: int | None = None
    put_delta: float | None = None


class OptionChain(BaseModel):
    symbol: str
    expiry: date
    rows: list[OptionRow]


class MarketDataProvider(Protocol):
    """Interface that all provider adapters implement."""
    name: str
    transport: str
    asset_classes: list[str]

    async def fetch_quote(self, symbol: str) -> Quote: ...
    async def fetch_bars(self, symbol: str, timeframe: str, count: int) -> list[Bar]: ...
    async def fetch_option_chain(self, symbol: str, expiry: date) -> OptionChain: ...
    async def health_check(self) -> dict: ...
