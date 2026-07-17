"""SPY Intelligence Aggregator — agent implementation."""
from __future__ import annotations


class SpyIntelligenceAggregatorAgent:
    """
    SPY Intelligence Aggregator.

    Layer: raw-intelligence/cross-market

    Implementation comes in STEP 4 per the order in
    docs/architecture/implementation-order.md.
    """

    agent_id = "raw-intelligence/cross-market.spy-intelligence-aggregator"
    layer = "raw-intelligence/cross-market"

    def __init__(self, config):
        self.config = config
