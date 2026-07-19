"""ARIMA Team Leader — agent implementation."""
from __future__ import annotations


class TeamLeaderAgent:
    """
    ARIMA Team Leader.

    Division: forecast
    Layer: 5-intelligence

    Implementation comes in STEP 4 per the order in
    docs/architecture/implementation-order.md.
    """

    agent_id = "forecast.arima.team-leader"
    division = "forecast"
    layer = "5-intelligence"

    def __init__(self, config):
        self.config = config
