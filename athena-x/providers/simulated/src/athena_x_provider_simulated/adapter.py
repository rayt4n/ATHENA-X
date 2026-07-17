"""Simulated market data provider adapter."""
from __future__ import annotations
from typing import Protocol


class SimulatedAdapter:
    """
    Simulated provider adapter.

    Implements the MarketDataProvider protocol defined in providers/base.py.
    Implementation comes in STEP 4 per the implementation order in
    docs/architecture/implementation-order.md.
    """

    name = "simulated"
    transport = "—"
    asset_classes = "all".split(", ")

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
