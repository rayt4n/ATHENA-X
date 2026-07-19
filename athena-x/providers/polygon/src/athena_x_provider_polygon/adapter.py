"""Polygon.io market data provider adapter."""
from __future__ import annotations
from typing import Protocol


class PolygonAdapter:
    """
    Polygon.io provider adapter.

    Implements the MarketDataProvider protocol defined in providers/base.py.
    Implementation comes in STEP 4 per the implementation order in
    docs/architecture/implementation-order.md.
    """

    name = "polygon"
    transport = "WebSocket"
    asset_classes = "equity, etf, currency, commodity".split(", ")

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
