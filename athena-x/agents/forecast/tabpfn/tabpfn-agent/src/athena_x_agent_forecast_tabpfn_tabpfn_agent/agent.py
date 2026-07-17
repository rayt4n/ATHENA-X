"""TabPFN Forecast AI — agent implementation."""
from __future__ import annotations


class TabpfnAgentAgent:
    """
    TabPFN Forecast AI.

    Division: forecast
    Layer: 5-intelligence

    Implementation comes in STEP 4 per the order in
    docs/architecture/implementation-order.md.
    """

    agent_id = "forecast.tabpfn.tabpfn-agent"
    division = "forecast"
    layer = "5-intelligence"

    def __init__(self, config):
        self.config = config
