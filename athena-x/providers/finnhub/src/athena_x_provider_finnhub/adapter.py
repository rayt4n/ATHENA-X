"""Finnhub market data provider adapter."""
from __future__ import annotations
from typing import Protocol


class FinnhubAdapter:
    """
    Finnhub provider adapter.

    Implements the MarketDataProvider protocol defined in providers/base.py.
    Implementation comes in STEP 4 per the implementation order in
    docs/architecture/implementation-order.md.
    """

    name = "finnhub"
    transport = "WebSocket"
    asset_classes = "equity, etf, currency".split(", ")

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
