"""RSI AI — agent implementation."""
from __future__ import annotations


class RsiAgent:
    """
    RSI AI.

    Layer: raw-intelligence/technical-analysis

    Implementation comes in STEP 4 per the order in
    docs/architecture/implementation-order.md.
    """

    agent_id = "raw-intelligence/technical-analysis.rsi"
    layer = "raw-intelligence/technical-analysis"

    def __init__(self, config):
        self.config = config
