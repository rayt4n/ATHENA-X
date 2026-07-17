"""EMA AI — agent implementation."""
from __future__ import annotations


class EmaAgentAgent:
    """
    EMA AI.

    Division: technical-analysis
    Layer: 5-intelligence

    Implementation comes in STEP 4 per the order in
    docs/architecture/implementation-order.md.
    """

    agent_id = "technical-analysis.indicator.ema-agent"
    division = "technical-analysis"
    layer = "5-intelligence"

    def __init__(self, config):
        self.config = config
