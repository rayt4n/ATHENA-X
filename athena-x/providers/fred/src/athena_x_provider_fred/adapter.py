"""FRED (St. Louis Fed) market data provider adapter."""
from __future__ import annotations
from typing import Protocol


class FredAdapter:
    """
    FRED (St. Louis Fed) provider adapter.

    Implements the MarketDataProvider protocol defined in providers/base.py.
    Implementation comes in STEP 4 per the implementation order in
    docs/architecture/implementation-order.md.
    """

    name = "fred"
    transport = "REST"
    asset_classes = "yield, macro indicators".split(", ")

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
