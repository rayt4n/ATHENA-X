"""TabPFN Team Leader — agent implementation."""
from __future__ import annotations


class TeamLeaderAgent:
    """
    TabPFN Team Leader.

    Division: forecast
    Layer: 5-intelligence

    Implementation comes in STEP 4 per the order in
    docs/architecture/implementation-order.md.
    """

    agent_id = "forecast.tabpfn.team-leader"
    division = "forecast"
    layer = "5-intelligence"

    def __init__(self, config):
        self.config = config
