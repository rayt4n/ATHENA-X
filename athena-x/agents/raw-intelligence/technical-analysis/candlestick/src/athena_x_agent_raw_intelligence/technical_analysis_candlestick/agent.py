"""Candlestick AI — agent implementation."""
from __future__ import annotations


class CandlestickAgent:
    """
    Candlestick AI.

    Layer: raw-intelligence/technical-analysis

    Implementation comes in STEP 4 per the order in
    docs/architecture/implementation-order.md.
    """

    agent_id = "raw-intelligence/technical-analysis.candlestick"
    layer = "raw-intelligence/technical-analysis"

    def __init__(self, config):
        self.config = config
