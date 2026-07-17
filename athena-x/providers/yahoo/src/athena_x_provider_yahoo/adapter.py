"""Yahoo Finance market data provider adapter."""
from __future__ import annotations
from typing import Protocol


class YahooAdapter:
    """
    Yahoo Finance provider adapter.

    Implements the MarketDataProvider protocol defined in providers/base.py.
    Implementation comes in STEP 4 per the implementation order in
    docs/architecture/implementation-order.md.
    """

    name = "yahoo"
    transport = "REST"
    asset_classes = "equity, etf, index, currency, commodity, yield, volatility, future".split(", ")

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
