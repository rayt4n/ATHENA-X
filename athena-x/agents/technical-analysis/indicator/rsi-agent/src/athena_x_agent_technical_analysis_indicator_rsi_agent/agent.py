"""RSI AI — agent implementation."""
from __future__ import annotations


class RsiAgentAgent:
    """
    RSI AI.

    Division: technical-analysis
    Layer: 5-intelligence

    Implementation comes in STEP 4 per the order in
    docs/architecture/implementation-order.md.
    """

    agent_id = "technical-analysis.indicator.rsi-agent"
    division = "technical-analysis"
    layer = "5-intelligence"

    def __init__(self, config):
        self.config = config
