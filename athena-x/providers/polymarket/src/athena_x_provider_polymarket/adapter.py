"""Polymarket market data provider adapter."""
from __future__ import annotations


class PolymarketAdapter:
    """
    Polymarket provider adapter.

    Layer 1 — Provider Adapters (STEP 3.5).
    ONLY downloads data. NEVER calculates, validates, or standardizes.
    Raw payloads are emitted to the bus and written to raw_landing schema.
    """

    name = "polymarket"
    transport = "REST"
    asset_classes = "prediction markets".split(", ")

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
